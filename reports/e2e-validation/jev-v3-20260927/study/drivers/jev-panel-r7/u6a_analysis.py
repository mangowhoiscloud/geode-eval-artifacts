"""Offline U6a item-accuracy connection to the pinned intent report and v1 analysis.

The frozen spec binds panel/meta/analyzer bytes and declares choice/ artifacts.
--record preserves every original attempt and appends the existing intent aggregate.
No model calls, credential reads, dispatch, or held-out inputs are needed.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import u0ci_analysis as admission_owner

REVISION = "2f2b494d605c9306dcf1d94a2394e7576e959ace"
UNIT = "U6a"
PRIMARY = "intent_joint_accuracy_delta"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def reports(
    source: Path, phase: Path, meta: Path, execution_receipt: Path, admission_spec: Path
) -> tuple[Any, Any, Any]:
    """Check frozen owners, runtime close, and retained helper admissions before aggregating."""
    frozen = load(phase / "freeze.json")
    require(frozen["unit"] == UNIT and frozen["source_revision"] == REVISION, "wrong freeze")
    for name in ("panel_driver.py", "track_common.py", "run_guards.py", "source_pin.py"):
        path = phase.parent / name
        require(frozen["sha256"].get(str(path)) == sha(path), f"driver changed: {name}")
    sys.path[:0] = [str(source), str(phase.parent)]
    driver = importlib.import_module("panel_driver")
    require(Path(driver.__file__).resolve().parent == phase.parent, "another driver was loaded")
    pinned, revision = driver.tc.pinned_source()
    require(pinned == source and revision == REVISION, "source pin differs")
    panel = importlib.import_module("evals.benchmarks.verdict_panel_runner")
    contract = importlib.import_module("scripts.eval.contract")
    handoff = importlib.import_module("evals.benchmarks.decision_handoff")
    require(Path(panel.__file__).resolve().is_relative_to(source), "another source was loaded")
    frozen, workloads = driver.preflight(UNIT)
    require(driver.phase_dir(UNIT).resolve() == phase, "phase differs from installed driver")
    require(
        (frozen["judgment"], frozen["mode"], frozen["max_concurrency"], frozen["lock_mode"])
        == ("intent", "paired-latency", 2, "panel-unit"),
        "wrong intent execution policy",
    )
    require(
        len(workloads) == 40 and len(frozen["cells"]) == 80,
        "U6a needs forty families/eighty calls",
    )
    spec_path = phase / "run-spec.choice.json"
    spec = contract.validate_run_spec(spec_path)
    require(
        spec["study"]["primary_metric"]["name"] == PRIMARY
        and spec["study"]["primary_metric"]["denominator"] == 220
        and spec["study"]["primary_metric"]["direction"] == "target",
        "wrong U6a metric",
    )
    for key, value in {
        "native_results": "choice/intent-results.json",
        "attempts": "choice/attempts.jsonl",
        "analysis": "choice/analysis.json",
    }.items():
        require(spec["artifacts"][key] == value, f"run-spec artifact path differs: {key}")
    panel_path = Path(frozen["states"])
    require(
        f"i-panel analysis sha256:{sha(panel_path)}"
        in spec["reproduction"]["environment"]["initial_state_ref"],
        "panel SHA not registered",
    )
    plan = spec["study"]["analysis_plan"]
    require(f"i-panel meta sha256:{sha(meta)}" in plan, "meta SHA not registered")
    require(
        f"U6a analysis entry sha256:{sha(Path(__file__))}" in plan,
        "analysis entry SHA not registered",
    )
    owner_sha = sha(Path(admission_owner.__file__))
    require(
        sha(phase.parent / "u0ci_analysis.py") == owner_sha
        and f"U6a receipt-check owner sha256:{owner_sha}" in plan,
        "receipt-check owner SHA not registered",
    )
    prior = admitted_prerequisite(contract, admission_spec, plan, spec)
    require(spec["run_id"] == frozen["run_ids"]["choice"], "run identity differs")
    done = load(execution_receipt)
    require(
        type(done.get("exit_code")) is int and done["exit_code"] == 0, "driver did not exit zero"
    )
    require(
        done.get("unit") == UNIT
        and done.get("source_revision") == REVISION
        and done.get("freeze_sha256") == sha(phase / "freeze.json")
        and done.get("driver_sha256") == frozen["driver_sha256"],
        "execution identity differs",
    )
    dispatch_path = phase / "dispatch-summary.json"
    dispatch = load(dispatch_path)
    # The pinned paired dispatcher counts planned cells, not replacement invocations.
    replacements = dispatch.get("substitutions")
    require(type(replacements) is int and 0 <= replacements <= 1, "replacement limit exceeded")
    require(
        dispatch.get("stopped") is False
        and dispatch.get("stop_reason") is None
        and dispatch.get("planned_calls") == 80
        and dispatch.get("dispatched_calls") == 80,
        "dispatch matrix incomplete",
    )
    block_path = phase / "private-receipts" / f"{spec['run_id']}-block.json"
    block = load(block_path)
    require(
        block.get("unit") == UNIT
        and block.get("run_id") == spec["run_id"]
        and block.get("source_revision") == REVISION
        and block.get("freeze_sha256") == sha(phase / "freeze.json"),
        "block identity differs",
    )
    require(
        block.get("lock_mode") == "panel-unit"
        and block.get("account_matches_g0") is True
        and block.get("planned_calls") == 80
        and block.get("dispatched_calls") == 80
        and block.get("stop_reason") is None,
        "execution guards not admitted",
    )
    # Account identity belongs to the hash-bound installed guard; no account is hard-coded here.
    run = phase / "choice"
    rows = contract.validate_attempts(run / "attempts.jsonl")
    require(
        len(rows) == 80 + replacements
        and all(
            row["change"]["surface"] == "judgment-panel" and row["run_id"] == spec["run_id"]
            for row in rows
        ),
        "expected original U6a attempts only, no aggregate",
    )
    selected = [row for row in rows if row["selected_for_analysis"]]
    unselected = [row for row in rows if not row["selected_for_analysis"]]
    require(len(selected) == 80 and len(unselected) == replacements, "selected call count differs")
    evidence_by_id = {
        row["attempt_id"]: evidence
        for row, evidence in panel._selected_judgments(run, "choice", selected_only=False)
    }
    for row in unselected:
        children = [child for child in selected if child["parent_attempt_id"] == row["attempt_id"]]
        require(
            row["validity"] == "invalid"
            and row["failure_class"] in panel.REPLACED_CLASSES
            and row["parent_attempt_id"] is None
            and len(children) == 1,
            "unselected attempt is not an allowed single replacement",
        )
        before, after = evidence_by_id[row["attempt_id"]], evidence_by_id[children[0]["attempt_id"]]
        require(
            all(
                before[key] == after[key]
                for key in (
                    "workload_id",
                    "state_id",
                    "cluster_id",
                    "variant",
                    "engine",
                    "primitive",
                )
            ),
            "replacement changed input identity",
        )
    require(
        all(
            row["parent_attempt_id"] in {None, *(r["attempt_id"] for r in unselected)}
            for row in selected
        ),
        "unexpected selected parent",
    )
    frozen_at = datetime.fromisoformat(spec["preregistration"]["frozen_at"].replace("Z", "+00:00"))
    require(
        all(
            row["timing"]["status"] == "exact"
            and datetime.fromisoformat(row["timing"]["started_at"].replace("Z", "+00:00"))
            >= frozen_at
            for row in rows
        ),
        "attempt timing predates freeze",
    )
    planned = {(c["workload_id"], c["engine"]): c for c in frozen["cells"]}
    states = {w.workload_id: w.state for w in workloads}
    seen = set()
    for row, evidence in panel._selected_judgments(run, "choice"):
        key = evidence["workload_id"], evidence["engine"]
        require(key in planned and key not in seen, "unexpected or duplicated cell")
        seen.add(key)
        cell = planned[key]
        require(
            all(evidence[k] == cell[k] for k in ("state_id", "cluster_id", "variant")),
            "cell identity changed",
        )
        require(row["validity"] == "valid", "selected infrastructure-invalid attempt")
        receipt = evidence.get("receipt")
        require(
            isinstance(receipt, dict) and receipt.get("contract") == handoff.INBOX_HELPER_CONTRACT,
            "helper receipt missing or contract differs",
        )
        engine = key[1]
        expected = (
            ("gpt-6-astra", "openai", "subscription")
            if engine == "llm"
            else ("jev-1.13.0", "typesafe", "payg")
        )
        require(
            (receipt.get("model"), receipt.get("provider"), receipt.get("source")) == expected,
            "helper route differs",
        )
        require(receipt["input_sha256"] == cell["case_sha256"], "helper input hash differs")
        admitted = evidence["status"] == "admitted"
        require(
            admitted == (receipt.get("accepted") is True) == (row["outcome"] == "passed"),
            "helper admission fields disagree",
        )
        if admitted:
            admission_owner.check_admitted(
                handoff, states[key[0]], engine, receipt, evidence, expected
            )
        else:
            require(
                evidence["status"] == "rejected" and row["failure_class"] == "invalid_judge_output",
                "rejection class differs",
            )
    require(seen == set(planned), "selected matrix incomplete")
    report = panel.intent_report(
        run,
        frozen["workload_ids"],
        panel=load(panel_path),
        meta=[json.loads(line) for line in meta.read_text().splitlines() if line.strip()],
        split_manifest_sha256=sha(panel_path),
    )
    require(
        report["planned_families"] == 40
        and report["planned_items"] == 220
        and report["primary"]["denominator"] == 220,
        "U6a item denominator differs",
    )
    report["analysis_provenance"] = {
        "source_revision": REVISION,
        "run_spec_sha256": sha(spec_path),
        "source_attempts_sha256": sha(run / "attempts.jsonl"),
        "freeze_sha256": sha(phase / "freeze.json"),
        "panel_sha256": sha(panel_path),
        "meta_sha256": sha(meta),
        "analysis_entry_sha256": sha(Path(__file__)),
        "receipt_check_owner_sha256": owner_sha,
        "admission_prerequisite": prior,
        "execution_receipt_sha256": sha(execution_receipt),
        "dispatch_summary_sha256": sha(dispatch_path),
        "block_receipt_sha256": sha(block_path),
        "strict_jev_sum_tolerance": 1e-5,
        "privacy_basis": "Pinned driver exit zero after its finally privacy check; "
        "not public-release approval",
    }
    return report, panel, contract


def admitted_prerequisite(contract: Any, admission_spec: Path, plan: str, spec: dict) -> dict:
    """The earlier 8/8 gate is a separate hash-bound bundle, not U6a's 220-item score."""
    contract.validate_run_bundle(admission_spec)
    prior_spec = load(admission_spec)
    prior_phase = admission_spec.parent
    prior_run = prior_phase / "choice"
    prior_analysis = load(prior_run / "analysis.json")
    prior_results = load(prior_run / "intent-results.json")
    require(
        f"U0c-i admission analysis sha256:{sha(prior_run / 'analysis.json')}" in plan,
        "admission analysis SHA not registered",
    )
    require(
        prior_spec["study"]["primary_metric"]["name"] == admission_owner.PRIMARY
        and prior_spec["reproduction"]["geode"]["revision"] == REVISION
        and load(prior_phase / "freeze.json")["unit"] == "U0c-i"
        and prior_results["admission"]["numerator"] == 8
        and prior_results["admission"]["denominator"] == 8
        and prior_results["admission"]["decision"] == "supported"
        and prior_analysis["decision"]["hypothesis_status"] == "supported",
        "U0c-i 8/8 prerequisite not passed",
    )
    require(
        datetime.fromisoformat(prior_analysis["analyzed_at"].replace("Z", "+00:00"))
        <= datetime.fromisoformat(spec["preregistration"]["frozen_at"].replace("Z", "+00:00")),
        "admission analysis must precede U6a freeze",
    )
    return {
        "run_id": prior_spec["run_id"],
        "run_spec_sha256": sha(admission_spec),
        "analysis_sha256": sha(prior_run / "analysis.json"),
        "results_sha256": sha(prior_run / "intent-results.json"),
        "admitted": 8,
        "planned_calls": 8,
    }


def record(phase: Path, report: dict[str, Any], panel: Any, contract: Any) -> None:
    run = phase / "choice"
    for name in (panel.INTENT_RESULTS, "analysis.json"):
        require(not (run / name).exists(), f"{name} already exists; preserve lineage")
    original = (run / "attempts.jsonl").read_bytes()
    panel.record_intent_aggregate(run, report)
    require((run / "attempts.jsonl").read_bytes().startswith(original), "original attempts changed")
    rows = contract.validate_attempts(run / "attempts.jsonl")
    selected = [row for row in rows if row["selected_for_analysis"]]
    refs = {json.dumps(ref, sort_keys=True): ref for row in rows for ref in row["evidence_refs"]}
    analysis = {
        "schema_id": "geode.eval-analysis@1",
        "schema_version": 1,
        "run_id": rows[0]["run_id"],
        "analyzed_at": datetime.now(UTC).isoformat(),
        "run_spec_sha256": sha(phase / "run-spec.choice.json"),
        "attempts_sha256": sha(run / "attempts.jsonl"),
        "selected_attempt_ids": [row["attempt_id"] for row in selected],
        "answer": "U6a measures the Jev minus Astra joint intent/target accuracy "
        "over 220 authored items in 40 families.",
        "metrics": panel.intent_metric_rows(report, primary=PRIMARY),
        "decision": {
            "outcome": "diagnostic-only",
            "hypothesis_status": report["primary"]["decision"],
            "rationale": "Pinned family-cluster bootstrap (2000 resamples; panel SHA seed); "
            "non-inferiority margin -0.05. U0c-i 8/8 is a separate prerequisite.",
        },
        "limitations": [
            "Forty author-visible families and 220 items support a diagnostic only, "
            "not held-out generalization, an E2E root result, or a latency claim.",
            "A rejected helper response counts every item in that family as wrong. "
            "Admission is not perfect helper accuracy.",
            "All original attempts and receipts are retained, including the permitted "
            "unselected infrastructure replacement; one extra attempt is analysis-only.",
        ],
        "evidence_refs": list(refs.values()),
    }
    panel._write_new(
        run / "analysis.json", json.dumps(analysis, ensure_ascii=False, indent=2) + "\n"
    )
    contract.validate_run_bundle(phase / "run-spec.choice.json")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--phase", type=Path, required=True)
    parser.add_argument("--meta", type=Path, required=True)
    parser.add_argument("--execution-receipt", type=Path, required=True)
    parser.add_argument("--admission-spec", type=Path, required=True)
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args(argv)
    phase = args.phase.resolve()
    report, panel, contract = reports(
        args.source.resolve(),
        phase,
        args.meta.resolve(),
        args.execution_receipt.resolve(),
        args.admission_spec.resolve(),
    )
    if args.record:
        record(phase, report, panel, contract)
    print(json.dumps({key: report[key] for key in ("primary", "admission", "engines")}, indent=2))
    return 0 if report["primary"]["value"] != "not-measurable" else 1


if __name__ == "__main__":
    raise SystemExit(main())
