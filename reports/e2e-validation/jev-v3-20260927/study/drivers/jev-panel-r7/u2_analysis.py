"""Private U2 frozen test analysis: source #2 reports, no fitting or dispatch.

--check-inputs reads public inputs only and rejects gold/alias arguments.
Analysis requires all U2/U2s/U3 exits and explicit --unseal-approved gold/aliases.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import subprocess
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REVISION = "2f2b494d605c9306dcf1d94a2394e7576e959ace"
ENGINES = ("llm", "jev")
CONDITIONS = ("has_contradiction", "missing_evidence")
PRIMARY = {
    "choice": "m7_choice_paired_accuracy_delta",
    "noul": "m7_noul_joint_accuracy_delta",
}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def owners(source: Path, phase: Path) -> tuple[Any, Any, Any, Any, dict[str, Any]]:
    def git(*args: str) -> str:
        return subprocess.run(  # noqa: S603 - fixed read-only git subcommands, no shell
            ["/usr/bin/git", "-C", str(source), *args], check=True, capture_output=True, text=True
        ).stdout.strip()

    require(git("rev-parse", "HEAD") == REVISION, "requires exact source #2")
    require(not git("status", "--porcelain"), "source #2 checkout is dirty")
    frozen = load(phase / "freeze.json")
    require(frozen["unit"] == "U2" and frozen["source_revision"] == REVISION, "wrong freeze")
    for name in ("panel_driver.py", "track_common.py", "source_pin.py", "run_guards.py"):
        path = phase.parent / name
        require(frozen["sha256"].get(str(path)) == sha(path), f"changed driver: {name}")
    sys.path[:0] = [str(source), str(phase.parent)]
    driver = importlib.import_module("panel_driver")
    require(Path(driver.__file__).resolve().parent == phase.parent, "different driver loaded")
    require(driver.phase_dir("U2").resolve() == phase, "not installed driver's u2")
    public_path(Path(frozen["states"]))
    frozen, _ = driver.preflight("U2")
    panel, metrics, contract, verifier = [
        importlib.import_module(name)
        for name in (
            "evals.benchmarks.verdict_panel_runner",
            "evals.benchmarks.decision_metrics",
            "scripts.eval.contract",
            "evals.benchmarks.decision_verification",
        )
    ]
    require(
        all(
            Path(m.__file__).resolve().is_relative_to(source)
            for m in (panel, metrics, contract, verifier)
        ),
        "different source imported",
    )
    return panel, metrics, contract, verifier, frozen


def public_path(path: Path) -> Path:
    path = path.resolve()
    require(
        not any("DO-NOT-OPEN" in p or "sealed" in p or p == "private-secrets" for p in path.parts),
        "protected input path; supply approved exported copies",
    )
    return path


def inputs(phase: Path, manifest: Path, selection: Path, frozen: dict, contract: Any) -> tuple:
    manifest, selection = public_path(manifest), public_path(selection)
    states_path = public_path(Path(frozen["states"]))
    public = load(manifest)
    test = public["splits"]["test"]
    require(
        (test["states"], test["headline_states"], test["out_of_envelope_states"]) == (240, 216, 24),
        "test split size differs",
    )
    require(sha(states_path) == test["states_sha256"], "public states hash differs")
    selected = load(selection)
    require(selected["schema_id"] == "geode.jev-selection-freeze@1", "selection freeze differs")
    specs = {}
    for primitive in PRIMARY:
        spec = contract.validate_run_spec(phase / f"run-spec.{primitive}.json")
        require(spec["run_id"] == frozen["run_ids"][primitive], "run identity differs")
        require(spec["reproduction"]["geode"]["revision"] == REVISION, "spec source differs")
        require(spec["preregistration"]["status"] == "frozen", "unfrozen spec")
        metric = spec["study"]["primary_metric"]
        require(
            (metric["name"], metric["denominator"], metric["direction"])
            == (PRIMARY[primitive], 216, "target"),
            "wrong primary",
        )
        require(
            spec["reproduction"]["execution"]["ordered_workload_ids"] == frozen["workload_ids"],
            "ordered workloads differ",
        )
        for bound in (
            f"U2 analysis entry sha256:{sha(Path(__file__))}",
            f"selection-freeze sha256: {sha(selection)}",
        ):
            require(bound in spec["study"]["analysis_plan"], "missing registered binding: " + bound)
        require(
            f"test public manifest sha256:{sha(manifest)}"
            in spec["reproduction"]["environment"]["initial_state_ref"],
            "manifest not bound",
        )
        for key, value in {
            "native_results": f"{primitive}/results.json",
            "attempts": f"{primitive}/attempts.jsonl",
            "analysis": f"{primitive}/analysis.json",
        }.items():
            require(spec["artifacts"][key] == value, "artifact path differs: " + key)
        specs[primitive] = spec
    require(
        len(frozen["workload_ids"]) == len(set(frozen["workload_ids"])) == 240
        and len(frozen["cells"]) == 960,
        "wrong planned test matrix",
    )
    return public, selected, specs


def closure(
    phase: Path, unit: str, receipt: Path, contract: Any, states_sha: str, selection_sha: str
) -> dict:
    """Finish all blinded calls before any explicit gold/alias read."""
    count, primitives = {
        "U2": (960, ("choice", "noul")),
        "U2s": (384, ("choice", "noul")),
        "U3": (240, ("choice",)),
    }[unit]
    frozen, done = load(phase / "freeze.json"), load(receipt)
    require(
        frozen["unit"] == unit and frozen["source_revision"] == REVISION, "closure freeze differs"
    )
    require(
        type(done.get("exit_code")) is int and done["exit_code"] == 0,
        "completed driver exit zero required",
    )
    require(
        done.get("unit") == unit
        and done.get("source_revision") == REVISION
        and done.get("freeze_sha256") == sha(phase / "freeze.json")
        and done.get("driver_sha256") == frozen["driver_sha256"],
        "closure receipt differs",
    )
    dispatch = load(phase / "dispatch-summary.json")
    substitutions = dispatch.get("substitutions")
    require(
        dispatch.get("stopped") is False
        and dispatch.get("stop_reason") is None
        and dispatch.get("planned_calls") == dispatch.get("dispatched_calls") == count
        and type(substitutions) is int
        and 0 <= substitutions / count <= 0.02,
        "incomplete or invalid dispatch",
    )
    block_path = phase / "private-receipts" / f"{frozen['run_ids']['choice']}-block.json"
    block = load(block_path)
    require(
        block.get("unit") == unit
        and block.get("run_id") == frozen["run_ids"]["choice"]
        and block.get("source_revision") == REVISION
        and block.get("freeze_sha256") == sha(phase / "freeze.json")
        and block.get("account_matches_g0") is True
        and block.get("lock_mode") == ("latency-solo" if unit == "U3" else "panel-unit")
        and block.get("planned_calls") == block.get("dispatched_calls") == count
        and block.get("stop_reason") is None,
        "closure block differs",
    )
    require(
        sha(public_path(Path(frozen["states"]))) == states_sha, "closure uses another test split"
    )
    original = []
    for primitive in primitives:
        spec = contract.validate_run_spec(phase / f"run-spec.{primitive}.json")
        require(
            spec["run_id"] == frozen["run_ids"][primitive]
            and f"selection-freeze sha256: {selection_sha}" in spec["study"]["analysis_plan"],
            "closure uses another run or selection freeze",
        )
        rows = contract.validate_attempts(phase / primitive / "attempts.jsonl")
        registered = datetime.fromisoformat(spec["preregistration"]["frozen_at"])
        require(
            all(
                r["run_id"] == spec["run_id"]
                and r["timing"]["status"] == "exact"
                and datetime.fromisoformat(r["timing"]["started_at"]) >= registered
                for r in rows
            ),
            "closure attempt identity/timing differs",
        )
        calls = [r for r in rows if r["change"]["surface"] == "judgment-panel"]
        require(
            sum(r["selected_for_analysis"] for r in calls) == count // len(primitives),
            "closure primitive count differs",
        )
        original.extend(calls)
    selected = [r for r in original if r["selected_for_analysis"]]
    require(
        len(original) == count + substitutions
        and len(selected) == count
        and all(r["validity"] == "valid" for r in selected),
        "closure attempts incomplete",
    )
    return {
        "unit": unit,
        "freeze_sha256": sha(phase / "freeze.json"),
        "execution_receipt_sha256": sha(receipt),
        "block_receipt_sha256": sha(block_path),
        "dispatch_summary_sha256": sha(phase / "dispatch-summary.json"),
    }


def unsealed_inputs(
    public: dict, frozen: dict, gold_path: Path, aliases: Path, panel: Any
) -> tuple:
    gold_path, aliases = public_path(gold_path), public_path(aliases)
    test = public["splits"]["test"]
    require(sha(gold_path) == test["gold_sha256"], "exported gold hash differs")
    require(sha(aliases) == test["aliases_sha256"], "exported aliases hash differs")
    states_list = jsonl(public_path(Path(frozen["states"])))
    states = {r["state_id"]: r for r in states_list}
    gold = panel.load_stability_gold(gold_path, aliases)
    require(
        len(states_list) == len(states) == 240
        and set(states) == set(frozen["workload_ids"]) == set(gold),
        "gold/state IDs differ",
    )
    require(
        all(r["split"] == "test" for r in states.values())
        and sum(r["headline"] is True for r in states.values()) == 216,
        "test partition differs",
    )
    return states, gold


def records(
    phase: Path,
    frozen: dict[str, Any],
    states: dict[str, Any],
    gold: dict[str, Any],
    specs: dict[str, Any],
    panel: Any,
    metrics: Any,
    contract: Any,
    verifier: Any,
) -> tuple[dict[str, Any], dict[str, Any]]:
    choice = {e: [] for e in ENGINES}
    noul = {e: {c: [] for c in CONDITIONS} for e in ENGINES}
    for primitive in PRIMARY:
        run = phase / primitive
        rows = contract.validate_attempts(run / "attempts.jsonl")
        require(all(r["run_id"] == specs[primitive]["run_id"] for r in rows), "mixed run IDs")
        require(
            all(r["change"]["surface"] == "judgment-panel" for r in rows),
            "aggregate exists; preserve recorded analysis",
        )
        registered = datetime.fromisoformat(specs[primitive]["preregistration"]["frozen_at"])
        require(
            all(
                r["timing"]["status"] == "exact"
                and datetime.fromisoformat(r["timing"]["started_at"]) >= registered
                for r in rows
            ),
            "attempt predates freeze or timing unknown",
        )
        planned = {
            (c["workload_id"], c["engine"]): c
            for c in frozen["cells"]
            if c["primitive"] == primitive
        }
        require(len(planned) == 480, "planned primitive matrix differs")
        observed = {}
        for row, evidence in panel._selected_judgments(run, primitive):
            key = (evidence["workload_id"], evidence["engine"])
            require(key in planned and key not in observed, "unexpected/duplicate selected cell")
            require(
                row["validity"] == "valid",
                "selected infrastructure invalid; no complete test analysis",
            )
            cell = planned[key]
            require(
                all(evidence[k] == cell[k] for k in ("state_id", "cluster_id", "variant")),
                "selected cell identity differs",
            )
            receipt = evidence["receipt"]
            expected = (
                ("gpt-6-astra", "openai", "subscription")
                if key[1] == "llm"
                else ("jev-1.13.0", "typesafe", "payg")
            )
            require(
                tuple(receipt[k] for k in ("model", "provider", "source")) == expected,
                "route mismatch",
            )
            require(
                receipt["input_sha256"] == cell["case_sha256"] == states[key[0]]["state_sha256"],
                "input digest mismatch",
            )
            require(
                receipt["question_sha256"]
                == verifier.contract_digests(primitive)["question_sha256"]
                and receipt["contract"] == verifier.CONTRACT_VERSION
                and receipt["sum_tolerance"] == 0.025,
                "question/contract/tolerance differs",
            )
            admitted = receipt["accepted"] is True
            require(
                admitted == (evidence["status"] == "admitted") == (row["outcome"] == "passed"),
                "admission fields disagree",
            )
            if admitted:
                require(
                    receipt["response_model"] == expected[0]
                    and receipt.get("response_provider") in (None, expected[1]),
                    "response route differs",
                )
                require(
                    evidence["stop_reason"] == ("completed" if key[1] == "llm" else "end_turn"),
                    "response termination differs",
                )
                require(
                    receipt["raw_answer_retention"] == "complete", "admitted raw answer omitted"
                )
                raw = receipt["raw_answer"]
                require(
                    hashlib.sha256(raw.encode()).hexdigest() == receipt["raw_answer_sha256"],
                    "answer digest differs",
                )
                decision = verifier.decide_answer(key[1], primitive, raw, sum_tolerance=0.025)
                require(
                    all(receipt[k] == decision[k] for k in ("verdict", "probabilities", "q")),
                    "retained decision differs",
                )
            else:
                require(
                    evidence["status"] == "rejected"
                    and row["failure_class"] == "invalid_judge_output",
                    "wrong rejection classification",
                )
            observed[key] = receipt
        require(
            set(observed) == set(planned), "incomplete selected matrix; no complete test analysis"
        )
        for state_id in frozen["workload_ids"]:
            for engine in ENGINES:
                if primitive == "choice":
                    choice[engine].append(
                        metrics.choice_record(
                            state_id,
                            states[state_id]["cluster_id"],
                            gold[state_id]["verdict"],
                            observed[state_id, engine],
                        )
                    )
                else:
                    items = metrics.condition_records(
                        state_id,
                        states[state_id]["cluster_id"],
                        {c: gold[state_id][c] for c in CONDITIONS},
                        observed[state_id, engine],
                    )
                    for condition in CONDITIONS:
                        noul[engine][condition].append(items[condition])
    return choice, noul


def probability_aux(records: Any, temperature: float | None, metrics: Any) -> dict:
    require(
        temperature is None
        or (type(temperature) in (int, float) and math.isfinite(temperature) and temperature > 0),
        "invalid frozen temperature",
    )
    corrected = metrics.scaled(records, temperature) if temperature is not None else None
    return {
        "temperature": temperature,
        "calibrated": {
            name: getattr(metrics, name)(corrected) if corrected is not None else None
            for name in ("brier", "nll", "ece")
        },
        "raw_risk_coverage": asdict(metrics.risk_coverage(records)),
    }


def reports(
    choice: Any, noul: Any, states: Any, selection: dict, manifest_sha: str, metrics: Any
) -> dict:
    """Frozen T affects only the three calibration auxiliaries; raw q owns all ranking."""
    tau = selection["cascade"]["tau"]
    require(
        tau is None or (type(tau) in (int, float) and math.isfinite(tau) and 0 <= tau <= 1),
        "invalid frozen tau",
    )
    choice_pairs = list(zip(choice["llm"], choice["jev"], strict=True))
    noul_pairs = list(
        zip(
            zip(*[noul["llm"][c] for c in CONDITIONS], strict=True),
            zip(*[noul["jev"][c] for c in CONDITIONS], strict=True),
            strict=True,
        )
    )
    output = {}
    for primitive, pairs in (("choice", choice_pairs), ("noul", noul_pairs)):
        scopes = {}
        for scope, headline in (("headline", True), ("outside", False)):
            filtered = [
                p
                for p in pairs
                if states[(p[0] if primitive == "choice" else p[0][0]).item_id]["headline"]
                is headline
            ]
            require(len(filtered) == (216 if headline else 24), "scope denominator differs")
            prefix = f"m7_{primitive}" if headline else f"m7_outside_{primitive}"
            if primitive == "choice":
                report = metrics.choice_panel_report(
                    filtered, split_manifest_sha256=manifest_sha, tau=tau, prefix=prefix
                )
                report["probability_aux"] = {
                    engine: probability_aux(
                        [p[index] for p in filtered],
                        selection["temperatures"]["choice"][engine]["temperature"],
                        metrics,
                    )
                    for index, engine in enumerate(ENGINES)
                }
            else:
                report = metrics.noul_panel_report(
                    filtered, split_manifest_sha256=manifest_sha, prefix=prefix
                )
                report["probability_aux"] = {
                    condition: {
                        engine: probability_aux(
                            [p[side][index] for p in filtered],
                            selection["temperatures"]["noul"][condition][engine]["temperature"],
                            metrics,
                        )
                        for side, engine in enumerate(ENGINES)
                    }
                    for index, condition in enumerate(CONDITIONS)
                }
                # Same registered cluster-bootstrap API and seed convention as Choice.
                report["condition_intervals"] = {}
                for index, condition in enumerate(CONDITIONS):
                    paired = [(p[0][index], p[1][index]) for p in filtered]
                    clusters = metrics._clusters_of(paired, lambda p: p[0].cluster_id)
                    statistics = {
                        "llm_auroc": lambda rows: metrics.auroc_error_detection(
                            [p[0] for p in rows]
                        ),
                        "jev_auroc": lambda rows: metrics.auroc_error_detection(
                            [p[1] for p in rows]
                        ),
                        **{
                            f"{name}_delta": metrics._paired(paired, getattr(metrics, metric))
                            for name, metric in (
                                ("auroc", "auroc_error_detection"),
                                ("brier", "brier"),
                                ("ece", "ece"),
                            )
                        },
                    }
                    report["condition_intervals"][condition] = {
                        name: metrics.cluster_bootstrap(
                            clusters,
                            statistic,
                            seed=metrics.bootstrap_seed(
                                manifest_sha, f"{prefix}_{condition}_{name}"
                            ),
                        ).as_dict()
                        for name, statistic in statistics.items()
                    }
            scopes[scope] = report
        document = {
            "primary": scopes["headline"]["primary"],
            **scopes,
            "hypothesis_status": scopes["headline"]["decision"],
            "probability_basis": "raw q for AUROC/risk/cascade; frozen selection T only "
            "for auxiliary Brier/NLL/ECE; no refit",
        }
        document["auxiliary_metrics"] = auxiliary_metrics(primitive, document)
        output[primitive] = document
    return output


def auxiliary_metrics(primitive: str, document: dict) -> dict:
    """Existing scalar (denominator one) or ratio binding, no alternate scoring formula."""
    result = {}

    def add(name: str, value: Any) -> None:
        if isinstance(value, dict):
            result[name] = (
                value
                if value["value"] is not None
                else {"value": "not-measurable", "numerator": None, "denominator": None}
            )
        else:
            result[name] = {
                "value": value if value is not None else "not-measurable",
                "numerator": value,
                "denominator": 1 if value is not None else None,
            }

    for scope in ("headline", "outside"):
        report = document[scope]
        groups = {"choice": report["engines"]} if primitive == "choice" else report["conditions"]
        for question, engines in groups.items():
            for engine, raw in engines.items():
                label = f"{scope}_{question}_{engine}"
                for name in ("accuracy", "brier", "nll", "ece", "auroc_error_detection"):
                    add(f"{label}_raw_{name}", raw[name])
                aux = (
                    report["probability_aux"][engine]
                    if primitive == "choice"
                    else report["probability_aux"][question][engine]
                )
                for name, value in aux["calibrated"].items():
                    add(f"{label}_calibrated_{name}", value)
                add(f"{label}_raw_aurc", aux["raw_risk_coverage"]["aurc"])
                for point, value in aux["raw_risk_coverage"]["risk_at"].items():
                    add(f"{label}_raw_risk_at_{point}", value)
        if primitive == "choice":
            for engine, value in report["macro_f1"].items():
                add(f"{scope}_{engine}_macro_f1", value)
            for name in ("accuracy", "coverage"):
                add(f"{scope}_cascade_{name}", report["cascade"].get(name))
        else:
            for engine in ENGINES:
                add(f"{scope}_{engine}_joint_accuracy", report["joint_accuracy"][engine])
                add(f"{scope}_{engine}_both_true_flagged", report["both_true_flagged"][engine])
    return result


def record(
    phase: Path, report: dict, specs: dict, panel: Any, contract: Any, bindings: dict
) -> None:
    require(
        not any(
            (phase / p / f).exists() for p in PRIMARY for f in ("results.json", "analysis.json")
        ),
        "derived output exists; preserve recorded lineage",
    )
    for primitive in PRIMARY:
        run = phase / primitive
        before = (run / "attempts.jsonl").read_bytes()
        document = {
            **report[primitive],
            "source_revision": REVISION,
            "inputs": bindings,
            "source_attempts_sha256": sha(run / "attempts.jsonl"),
        }
        panel._record_aggregate(
            run,
            "results.json",
            document,
            failure_class=None,
            description="U2 frozen test analysis; zero model dispatches and no fitting.",
            expected_effect="Headline 216 and outside 24 stay separate.",
            observed=("Complete paired test matrix.", "Incomplete test matrix."),
        )
        require(
            (run / "attempts.jsonl").read_bytes().startswith(before), "original attempts changed"
        )
        rows = contract.validate_attempts(run / "attempts.jsonl")
        selected = [r for r in rows if r["selected_for_analysis"]]
        refs = {json.dumps(ref, sort_keys=True): ref for r in rows for ref in r["evidence_refs"]}
        metric_rows = [
            panel._bound_row(
                PRIMARY[primitive],
                document["primary"],
                "/primary",
                unit="ratio",
                source_ref="results.json",
            )
        ]
        metric_rows.extend(
            panel._bound_row(
                name, value, f"/auxiliary_metrics/{name}", unit="ratio", source_ref="results.json"
            )
            for name, value in document["auxiliary_metrics"].items()
        )
        analysis = {
            "schema_id": "geode.eval-analysis@1",
            "schema_version": 1,
            "run_id": specs[primitive]["run_id"],
            "analyzed_at": datetime.now(UTC).isoformat(),
            "run_spec_sha256": sha(phase / f"run-spec.{primitive}.json"),
            "attempts_sha256": sha(run / "attempts.jsonl"),
            "selected_attempt_ids": [r["attempt_id"] for r in selected],
            "answer": "Frozen held-out panel comparison; headline 216 and outside 24 "
            "are reported separately.",
            "metrics": metric_rows,
            "decision": {
                "outcome": "diagnostic-only",
                "hypothesis_status": document["hypothesis_status"],
                "rationale": specs[primitive]["study"]["decision_rule"],
            },
            "limitations": [
                "Results use explicit approved exported gold only after U2/U2s/U3 closure.",
                "Frozen selection T affects only auxiliary Brier/NLL/ECE; no refit or new tau.",
                "Signed outside delta and interval bounds remain in native results, because v1 "
                "secondary metric numerators cannot be negative. No sign clipping is applied.",
                "Infrastructure-stopped runs require separate failure analysis; "
                "no missing cell fill.",
                "Shared account external usage is unknown; this is not publication approval.",
            ],
            "evidence_refs": list(refs.values()),
        }
        panel._write_new(
            run / "analysis.json", json.dumps(analysis, ensure_ascii=False, indent=2) + "\n"
        )
        contract.validate_run_bundle(phase / f"run-spec.{primitive}.json")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "phase", "manifest", "selection-freeze"):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in (
        "gold",
        "aliases",
        "execution-receipt",
        "u2s-phase",
        "u2s-execution-receipt",
        "u3-phase",
        "u3-execution-receipt",
    ):
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("--unseal-approved", action="store_true")
    parser.add_argument("--check-inputs", action="store_true")
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args(argv)
    require(
        not (
            args.check_inputs and (args.record or args.gold or args.aliases or args.unseal_approved)
        ),
        "check-inputs accepts public inputs only",
    )
    source, phase = args.source.resolve(), public_path(args.phase)
    panel, metrics, contract, verifier, frozen = owners(source, phase)
    public, selection, specs = inputs(phase, args.manifest, args.selection_freeze, frozen, contract)
    if args.check_inputs:
        print(
            json.dumps(
                {
                    "ready": True,
                    "planned_calls": 960,
                    "headline": 216,
                    "outside": 24,
                    "analysis_entry_sha256": sha(Path(__file__)),
                    "model_calls": 0,
                }
            )
        )
        return 0
    require(
        args.unseal_approved and args.gold and args.aliases,
        "explicit unseal approval and exported gold/aliases required",
    )
    require(
        all(
            (
                args.execution_receipt,
                args.u2s_phase,
                args.u2s_execution_receipt,
                args.u3_phase,
                args.u3_execution_receipt,
            )
        ),
        "all blinded-unit exit receipts required",
    )
    close_args = (contract, public["splits"]["test"]["states_sha256"], sha(args.selection_freeze))
    closures = [
        closure(phase, "U2", args.execution_receipt, *close_args),
        closure(public_path(args.u2s_phase), "U2s", args.u2s_execution_receipt, *close_args),
        closure(public_path(args.u3_phase), "U3", args.u3_execution_receipt, *close_args),
    ]
    states, gold = unsealed_inputs(public, frozen, args.gold, args.aliases, panel)
    choice, noul = records(phase, frozen, states, gold, specs, panel, metrics, contract, verifier)
    result = reports(choice, noul, states, selection, sha(args.manifest), metrics)
    bindings = {
        "manifest_sha256": sha(args.manifest),
        "selection_freeze_sha256": sha(args.selection_freeze),
        "gold_sha256": sha(args.gold),
        "aliases_sha256": sha(args.aliases),
        "analysis_entry_sha256": sha(Path(__file__)),
        "completed_units": closures,
        "unseal_approved_by_operator": True,
    }
    if args.record:
        record(phase, result, specs, panel, contract, bindings)
    print(json.dumps({p: r["primary"] for p, r in result.items()}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
