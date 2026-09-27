"""Private U1 analysis entry: existing metrics, selected native receipts, no dispatch.

--check-inputs validates frozen inputs before calls. Default reads completed U1.
--record appends only analysis aggregates and writes immutable selection-freeze.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REVISION = "2f2b494d605c9306dcf1d94a2394e7576e959ace"
ENGINES = ("llm", "jev")
CONDITIONS = ("has_contradiction", "missing_evidence")
FIT_SCOPE = "U1 fit scope: all 160 selection states; primary 144 headline; outside 16 descriptive."
PRIMARY = {
    "choice": "m7sel_choice_paired_accuracy_delta",
    "noul": "m7sel_noul_joint_accuracy_delta",
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
    require(frozen["unit"] == "U1" and frozen["source_revision"] == REVISION, "wrong freeze")
    for name in ("panel_driver.py", "track_common.py", "source_pin.py", "run_guards.py"):
        path = phase.parent / name
        require(frozen["sha256"].get(str(path)) == sha(path), f"changed driver: {name}")
    sys.path[:0] = [str(source), str(phase.parent)]
    driver = importlib.import_module("panel_driver")
    require(Path(driver.__file__).resolve().parent == phase.parent, "different driver loaded")
    require(driver.phase_dir("U1").resolve() == phase, "not installed driver's u1")
    frozen, _ = driver.preflight("U1")
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


def inputs(
    phase: Path, manifest: Path, gold_path: Path, frozen: dict[str, Any], contract: Any
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    # Refuse protected/test gold before reading any input bytes.
    states_path = Path(frozen["states"])
    require(
        not any(
            "DO-NOT-OPEN" in part or "sealed" in part or part == "private-secrets"
            for path in (manifest, gold_path, states_path)
            for part in path.parts
        ),
        "protected input path",
    )
    require(gold_path.name == "gold.selection.jsonl", "only named selection gold is allowed")
    require(
        not any(
            "DO-NOT-OPEN" in p or "sealed" in p or p == "private-secrets" for p in gold_path.parts
        ),
        "protected gold path",
    )
    manifest_data = load(manifest)
    selection = manifest_data["splits"]["selection"]
    require(selection["sealed_gold"] is False, "selection gold must be unsealed")
    require(
        (selection["states"], selection["headline_states"], selection["out_of_envelope_states"])
        == (160, 144, 16),
        "selection size differs",
    )
    require(sha(states_path) == selection["states_sha256"], "selection states hash differs")
    require(sha(gold_path) == selection["gold_sha256"], "selection gold hash differs")
    states_list, gold_list = jsonl(states_path), jsonl(gold_path)
    states = {r["state_id"]: r for r in states_list}
    gold = {r["state_id"]: r for r in gold_list}
    ids = frozen["workload_ids"]
    require(
        len(ids) == len(set(ids)) == len(states) == len(states_list) == 160,
        "planned states duplicate or missing",
    )
    require(set(ids) == set(states) == set(gold) and len(gold_list) == 160, "gold/state IDs differ")
    require(all(r["split"] == "selection" for r in states.values()), "non-selection state")
    require(sum(r["headline"] is True for r in states.values()) == 144, "headline differs")
    specs = {}
    for primitive in PRIMARY:
        spec = contract.validate_run_spec(phase / f"run-spec.{primitive}.json")
        require(spec["run_id"] == frozen["run_ids"][primitive], "run identity differs")
        require(spec["preregistration"]["status"] == "frozen", "unfrozen spec")
        require(spec["reproduction"]["geode"]["revision"] == REVISION, "spec source differs")
        metric = spec["study"]["primary_metric"]
        require(
            metric["name"] == PRIMARY[primitive] and metric["denominator"] == 144,
            "primary name/denominator differs",
        )
        require(
            spec["reproduction"]["execution"]["ordered_workload_ids"] == ids,
            "workload order differs",
        )
        plan = spec["study"]["analysis_plan"]
        for bound in (
            FIT_SCOPE,
            f"U1 analysis entry sha256:{sha(Path(__file__))}",
            f"selection manifest sha256:{sha(manifest)}",
            f"selection gold sha256:{sha(gold_path)}",
        ):
            require(bound in plan, "missing registered input/entry/fit scope: " + bound)
        specs[primitive] = spec
    return states, gold, specs


def execution_guard(phase: Path, frozen: dict[str, Any], receipt: Path) -> dict[str, str]:
    done = load(receipt)
    require(
        type(done.get("exit_code")) is int and done["exit_code"] == 0,
        "driver exit receipt is not zero",
    )
    require(
        done.get("unit") == "U1" and done.get("source_revision") == REVISION,
        "execution identity differs",
    )
    require(
        done.get("freeze_sha256") == sha(phase / "freeze.json")
        and done.get("driver_sha256") == frozen["driver_sha256"],
        "execution hashes differ",
    )
    dispatch_path = phase / "dispatch-summary.json"
    dispatch = load(dispatch_path)
    require(
        dispatch.get("stopped") is False and dispatch.get("stop_reason") is None,
        "dispatch did not complete; no fitting allowed",
    )
    require(
        dispatch["planned_calls"] == dispatch["dispatched_calls"] == 640,
        "dispatch matrix incomplete",
    )
    require(dispatch["substitutions"] / 640 <= 0.02, "substitution ceiling exceeded")
    block_path = phase / "private-receipts" / f"{frozen['run_ids']['choice']}-block.json"
    block = load(block_path)
    require(
        block.get("unit") == "U1" and block.get("run_id") == frozen["run_ids"]["choice"],
        "block identity differs",
    )
    require(
        block.get("source_revision") == REVISION
        and block.get("freeze_sha256") == sha(phase / "freeze.json")
        and block.get("lock_mode") == "panel-unit"
        and block.get("account_matches_g0") is True,
        "block guard identity differs",
    )
    require(
        block.get("planned_calls") == block.get("dispatched_calls") == 640
        and block.get("stop_reason") is None,
        "block matrix incomplete",
    )
    return {
        "process_receipt": sha(receipt),
        "dispatch_summary": sha(dispatch_path),
        "private_block_receipt": sha(block_path),
    }


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
        require(len(planned) == 320, "planned primitive matrix differs")
        observed = {}
        for row, evidence in panel._selected_judgments(run, primitive):
            key = (evidence["workload_id"], evidence["engine"])
            require(key in planned and key not in observed, "unexpected/duplicate selected cell")
            require(row["validity"] == "valid", "selected infrastructure invalid; no fitting")
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
        require(set(observed) == set(planned), "incomplete selected matrix; no fitting")
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


def reports(choice: Any, noul: Any, states: Any, manifest_sha: str, metrics: Any) -> dict[str, Any]:
    result = {}
    choice_pairs = list(zip(choice["llm"], choice["jev"], strict=True))
    noul_pairs = list(
        zip(
            zip(*[noul["llm"][c] for c in CONDITIONS], strict=True),
            zip(*[noul["jev"][c] for c in CONDITIONS], strict=True),
            strict=True,
        )
    )
    for primitive, pairs in (("choice", choice_pairs), ("noul", noul_pairs)):
        strata = {}
        for scope, headline in (("headline", True), ("outside", False)):
            filtered = [
                p
                for p in pairs
                if states[(p[0] if primitive == "choice" else p[0][0]).item_id]["headline"]
                is headline
            ]
            prefix = f"m7sel_{primitive}" if headline else f"m7sel_outside_{primitive}"
            if primitive == "choice":
                report = metrics.choice_panel_report(
                    filtered, split_manifest_sha256=manifest_sha, tau=None, prefix=prefix
                )
                report.pop("cascade")  # Fitted cascade lives only in selection-freeze.
            else:
                report = metrics.noul_panel_report(
                    filtered, split_manifest_sha256=manifest_sha, prefix=prefix
                )
            report["decision"] = "mixed"  # U1 has no hypothesis test, irrespective of bootstrap.
            strata[scope] = report
        result[primitive] = {
            "primary": strata["headline"]["primary"],
            **strata,
            "hypothesis_status": "mixed",
            "fit_scope": FIT_SCOPE,
        }
    return result


def before_test_calls(phase: Path) -> None:
    """Do not refit after a test/externally scored panel has begun in this program."""
    for runner_root in phase.parent.parent.glob("jev-panel*"):
        for unit in ("u2", "u2s", "u3", "x1"):
            directory = runner_root / unit
            require(
                not (directory / "session" / "dispatch-log.jsonl").exists()
                and not any(directory.glob("*/attempts.jsonl")),
                "test/external panel has started; selection fitting prohibited",
            )


def record(
    phase: Path,
    report: dict[str, Any],
    specs: Any,
    choice: Any,
    noul: Any,
    panel: Any,
    metrics: Any,
    contract: Any,
    bindings: dict[str, str],
) -> None:
    before_test_calls(phase)
    paths = [phase / p / f for p in PRIMARY for f in ("results.json", "analysis.json")]
    paths += [phase / "selection-freeze.json"]
    require(not any(p.exists() for p in paths), "derived output exists; no overwrite/refit")
    for primitive in PRIMARY:
        run = phase / primitive
        document = {
            **report[primitive],
            "source_revision": REVISION,
            "inputs": bindings,
            "source_attempts_sha256": sha(run / "attempts.jsonl"),
        }
        before = (run / "attempts.jsonl").read_bytes()
        panel._record_aggregate(
            run,
            "results.json",
            document,
            failure_class=None,
            description="U1 selection analysis only; zero model dispatches.",
            expected_effect="Bind headline 144 and outside 16; no selection hypothesis test.",
            observed=("Complete paired selection matrix.", "Incomplete selection matrix."),
        )
        require(
            (run / "attempts.jsonl").read_bytes().startswith(before), "original attempts changed"
        )
        rows = contract.validate_attempts(run / "attempts.jsonl")
        selected = [r for r in rows if r["selected_for_analysis"]]
        refs = {
            json.dumps(ref, sort_keys=True): ref for r in selected for ref in r["evidence_refs"]
        }
        analysis = {
            "schema_id": "geode.eval-analysis@1",
            "schema_version": 1,
            "run_id": specs[primitive]["run_id"],
            "analyzed_at": datetime.now(UTC).isoformat(),
            "run_spec_sha256": sha(phase / f"run-spec.{primitive}.json"),
            "attempts_sha256": sha(run / "attempts.jsonl"),
            "selected_attempt_ids": [r["attempt_id"] for r in selected],
            "answer": "Selection diagnostics only; T and tau are fitted once before test calls.",
            "metrics": [
                panel._bound_row(
                    PRIMARY[primitive],
                    document["primary"],
                    "/primary",
                    unit="ratio",
                    source_ref="results.json",
                )
            ],
            "decision": {
                "outcome": "diagnostic-only",
                "hypothesis_status": "mixed",
                "rationale": specs[primitive]["study"]["decision_rule"],
            },
            "limitations": [
                FIT_SCOPE,
                "Authored selection split; no test or external claim.",
                "Whole provider dispatch/account coverage is not inferred.",
            ],
            "evidence_refs": list(refs.values()),
        }
        panel._write_new(
            run / "analysis.json", json.dumps(analysis, ensure_ascii=False, indent=2) + "\n"
        )
        contract.validate_analysis(
            run / "analysis.json",
            run_spec_path=phase / f"run-spec.{primitive}.json",
            attempts_path=run / "attempts.jsonl",
        )
    freeze_inputs = dict(bindings)
    for primitive in PRIMARY:
        for filename in ("attempts.jsonl", "analysis.json"):
            freeze_inputs[f"{primitive}/{filename}"] = sha(phase / primitive / filename)
    freeze = metrics.selection_freeze(choice=choice, noul=noul, inputs=freeze_inputs)
    panel._write_new(
        phase / "selection-freeze.json", json.dumps(freeze, ensure_ascii=False, indent=2) + "\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "phase", "manifest", "gold"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--execution-receipt", type=Path)
    parser.add_argument("--check-inputs", action="store_true")
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args()
    require(not (args.record and args.check_inputs), "choose check-inputs or record")
    source, phase, manifest, gold_path = [
        p.resolve() for p in (args.source, args.phase, args.manifest, args.gold)
    ]
    panel, metrics, contract, verifier, frozen = owners(source, phase)
    states, gold, specs = inputs(phase, manifest, gold_path, frozen, contract)
    if args.check_inputs:
        print(
            json.dumps(
                {
                    "ready": True,
                    "planned_calls": 640,
                    "headline": 144,
                    "outside": 16,
                    "fit_scope": FIT_SCOPE,
                    "analysis_entry_sha256": sha(Path(__file__)),
                }
            )
        )
        return 0
    require(
        args.execution_receipt is not None, "completed process receipt required before analysis"
    )
    bindings = execution_guard(phase, frozen, args.execution_receipt)
    bindings.update(
        {
            "selection_manifest": sha(manifest),
            "selection_gold": sha(gold_path),
            "source_freeze": sha(phase / "freeze.json"),
            "analysis_entry": sha(Path(__file__)),
        }
    )
    choice, noul = records(phase, frozen, states, gold, specs, panel, metrics, contract, verifier)
    report = reports(choice, noul, states, sha(manifest), metrics)
    if args.record:
        record(phase, report, specs, choice, noul, panel, metrics, contract, bindings)
    print(json.dumps({p: r["primary"] for p, r in report.items()}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
