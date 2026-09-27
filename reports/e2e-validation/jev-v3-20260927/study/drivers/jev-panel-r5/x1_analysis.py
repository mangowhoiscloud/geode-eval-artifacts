"""Guarded X1 native analysis plus the existing eval-analysis contract; no dispatch.

X1a evidence and selection bytes are verified before native analysis can read gold.
Only the approved analysis invocation reads gold; T/tau are never fitted here.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import track_common as tc

HERE = Path(__file__).resolve().parent
REVISION = "2f2b494d605c9306dcf1d94a2394e7576e959ace"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def digest_binding(plan: str, label: str, path: Path) -> None:
    key = label + " sha256:"
    values = re.findall(re.escape(key) + r" ([0-9a-f]{64})(?=[.;\s]|$)", plan)
    require(plan.count(key) == 1 and values == [tc.sha(path)], f"{label} digest differs")


def x1a_gate(spec_path: Path, process: Path, plan: str, contract: Any) -> dict[str, str]:
    """Consume the already recorded 4/4 admission, preserving its original producer."""
    phase = spec_path.resolve().parent
    analysis_path = phase / "choice/analysis.json"
    digest_binding(plan, "X1a admission analysis", analysis_path)
    contract.validate_run_bundle(spec_path)
    spec = contract.validate_run_spec(spec_path)
    frozen = tc.read(phase / "freeze.json")
    tc.check_bound(frozen["sha256"])
    report_path = phase / "choice/results.json"
    report = tc.read(report_path)
    require(
        spec["study"]["primary_metric"]["name"] == "x1_admission_admitted_ratio"
        and spec["study"]["primary_metric"]["denominator"] == 4
        and frozen["unit"] == "X1a"
        and frozen["source_revision"] == REVISION
        and report["primary"] == {"value": 1.0, "numerator": 4, "denominator": 4}
        and report["admission_gate_passed"] is True
        and report["measurable"] is True,
        "X1a must have the recorded complete 4/4 admission",
    )
    require(
        report["run_id"] == spec["run_id"] == frozen["run_ids"]["choice"]
        and report["source_revision"] == REVISION
        and report["source_freeze_sha256"] == tc.sha(phase / "freeze.json")
        and report["source_run_spec_sha256"] == tc.sha(spec_path),
        "X1a report source binding differs",
    )
    rows = contract.validate_attempts(phase / "choice/attempts.jsonl")
    original = rows[:-1]
    require(
        len(rows) == 5
        and rows[-1]["change"]["surface"] == "analysis-only"
        and all(
            r["change"]["surface"] == "judgment-panel"
            and r["selected_for_analysis"]
            and r["validity"] == "valid"
            and r["outcome"] == "passed"
            for r in original
        ),
        "X1a needs four admitted original attempts and one analysis aggregate",
    )
    import hashlib

    original_bytes = b"".join((phase / "choice/attempts.jsonl").read_bytes().splitlines(True)[:-1])
    require(
        hashlib.sha256(original_bytes).hexdigest() == report["source_attempts_sha256"],
        "X1a original attempts digest differs",
    )
    entry_path = phase.parent / "x1a_admission_analysis.py"
    entry_sha = tc.sha(entry_path)
    require(
        report["analysis_entry_sha256"] == entry_sha
        and f"X1a analysis entry sha256:{entry_sha}" in spec["study"]["analysis_plan"],
        "X1a producer digest differs",
    )
    module_spec = importlib.util.spec_from_file_location("_frozen_x1a_owner", entry_path)
    require(module_spec is not None and module_spec.loader is not None, "X1a owner unavailable")
    owner = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(owner)
    execution = owner.execution_guard(phase, frozen, process)
    require(
        execution == report["execution_guard"] and execution["verified"] is True,
        "X1a completed execution binding differs",
    )
    return {
        "admission_analysis_sha256": tc.sha(analysis_path),
        "admission_results_sha256": tc.sha(report_path),
        "admission_freeze_sha256": tc.sha(phase / "freeze.json"),
        "admission_process_sha256": tc.sha(process),
    }


def x1_execution(phase: Path, frozen: dict[str, Any], process: Path) -> None:
    done = tc.read(process)
    require(
        type(done.get("exit_code")) is int and done["exit_code"] == 0, "X1 driver did not exit zero"
    )
    require(
        done.get("unit") == "X1"
        and done.get("source_revision") == REVISION
        and done.get("freeze_sha256") == tc.sha(phase / "freeze.json")
        and done.get("driver_sha256") == frozen["driver_sha256"],
        "X1 exit identity differs",
    )
    summary = tc.read(phase / "dispatch-summary.json")
    substitutions = summary.get("substitutions")
    require(
        type(substitutions) is int and 0 <= substitutions <= 0.02 * 478,
        "X1 substitutions exceed the frozen ceiling",
    )
    require(
        summary.get("stopped") is False
        and summary.get("stop_reason") is None
        and summary.get("planned_calls") == 478
        and summary.get("dispatched_calls") == 478,
        "X1 dispatch matrix incomplete",
    )
    block = tc.read(phase / "private-receipts" / f"{frozen['run_ids']['choice']}-block.json")
    require(
        block.get("unit") == "X1"
        and block.get("run_id") == frozen["run_ids"]["choice"]
        and block.get("source_revision") == REVISION
        and block.get("freeze_sha256") == tc.sha(phase / "freeze.json")
        and block.get("account_matches_g0") is True
        and block.get("lock_mode") == "panel-unit"
        and block.get("planned_calls") == 478
        and block.get("dispatched_calls") == 478
        and block.get("stop_reason") is None,
        "X1 execution guard differs",
    )


def record_analysis(spec_path: Path, run: Path, native: Any, panel: Any, contract: Any) -> None:
    spec = contract.validate_run_spec(spec_path)
    report = tc.read(run / native.RESULTS)
    rows = contract.validate_attempts(run / "attempts.jsonl")
    selected = [row for row in rows if row["selected_for_analysis"]]
    refs = {json.dumps(ref, sort_keys=True): ref for row in rows for ref in row["evidence_refs"]}
    metrics = native.x1_metric_rows(report)
    require(metrics[0]["name"] == spec["study"]["primary_metric"]["name"], "primary differs")
    doc = {
        "schema_id": "geode.eval-analysis@1",
        "schema_version": 1,
        "run_id": spec["run_id"],
        "analyzed_at": datetime.now(UTC).isoformat(),
        "run_spec_sha256": tc.sha(spec_path),
        "attempts_sha256": tc.sha(run / "attempts.jsonl"),
        "selected_attempt_ids": [row["attempt_id"] for row in selected],
        "answer": "External X1 binary verdict diagnostic with the preregistered native metrics.",
        "metrics": metrics,
        "decision": {
            "outcome": "diagnostic-only",
            "hypothesis_status": report["decision"],
            "rationale": spec["study"]["decision_rule"],
        },
        "limitations": [
            "External correctness analysis only; no latency or general benchmark claim.",
            "T and tau are read from the frozen selection artifact, never refitted.",
            "Descriptive auxiliary metrics do not add hypothesis tests.",
        ],
        "evidence_refs": list(refs.values()),
    }
    panel._write_new(run / "analysis.json", json.dumps(doc, ensure_ascii=False, indent=2) + "\n")
    contract.validate_run_bundle(spec_path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in (
        "run-spec",
        "choice",
        "manifest",
        "states",
        "gold",
        "selection-freeze",
        "admission-spec",
        "admission-execution-receipt",
        "execution-receipt",
    ):
        parser.add_argument("--" + flag, type=Path, required=True)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args(argv)
    source, revision = tc.pinned_source()
    require(revision == REVISION, "requires exact source #2")
    import panel_driver
    from evals.benchmarks import external_binary as native
    from evals.benchmarks import verdict_panel_runner as panel
    from scripts.eval import contract

    require(Path(panel.__file__).resolve().is_relative_to(source), "another source was loaded")

    phase = args.run_spec.resolve().parent
    require(
        phase == panel_driver.phase_dir("X1").resolve()
        and args.choice.resolve() == phase / "choice",
        "X1 path differs from installed driver",
    )
    frozen, _ = panel_driver.preflight("X1")
    require(
        frozen["planned_calls"] == 478
        and len(frozen["workload_ids"]) == 239
        and set(frozen["run_ids"]) == {"choice"},
        "X1 must retain the 239-state matrix",
    )
    spec = contract.validate_run_spec(args.run_spec)
    tc.check_spec(
        spec,
        prefix="geode-jev-external-cuavb-choice-",
        revision=revision,
        driver_sha256=tc.sha(Path(__file__)),
        max_concurrency=4,
    )
    require(
        spec["run_id"] == frozen["run_ids"]["choice"]
        and spec["study"]["primary_metric"]["name"] == native.PRIMARY
        and spec["study"]["primary_metric"]["denominator"] == 239,
        "X1 primary differs",
    )
    require(
        all(
            spec["artifacts"].get(k) == v
            for k, v in {
                "native_results": "choice/x1-results.json",
                "attempts": "choice/attempts.jsonl",
                "analysis": "choice/analysis.json",
            }.items()
        ),
        "X1 artifact paths differ",
    )
    plan = spec["study"]["analysis_plan"]
    digest_binding(plan, "selection-freeze", args.selection_freeze)
    selection = tc.read(args.selection_freeze)
    native.frozen_tau(selection)
    native.frozen_temperatures(selection)
    require(args.states.resolve() == Path(frozen["states"]).resolve(), "X1 states differ")
    require(
        f"x1 manifest sha256:{tc.sha(args.manifest)}"
        in spec["reproduction"]["environment"]["initial_state_ref"],
        "X1 manifest differs",
    )
    x1a_gate(args.admission_spec, args.admission_execution_receipt, plan, contract)
    x1_execution(phase, frozen, args.execution_receipt)
    run = args.choice.resolve()
    require(
        not (run / native.RESULTS).exists() and not (run / "analysis.json").exists(),
        "X1 derived output exists; refuse repeated aggregation",
    )
    rows = contract.validate_attempts(run / "attempts.jsonl")
    require(
        all(
            row["change"]["surface"] == "judgment-panel" and row["run_id"] == spec["run_id"]
            for row in rows
        ),
        "X1 original attempts required",
    )
    substitutions = tc.read(phase / "dispatch-summary.json")["substitutions"]
    require(
        len(rows) == 478 + substitutions
        and sum(row["selected_for_analysis"] for row in rows) == 478,
        "X1 attempt and substitution counts differ",
    )
    original = (run / "attempts.jsonl").read_bytes()
    native_args = []
    for flag in (
        "run-spec",
        "choice",
        "manifest",
        "states",
        "gold",
        "selection-freeze",
        "reference",
    ):
        value = getattr(args, flag.replace("-", "_"))
        if value is not None:
            native_args.extend(["--" + flag, str(value)])
    if args.record:
        native_args.append("--record")
    code = native.main(native_args)
    if args.record:
        require(
            (run / "attempts.jsonl").read_bytes().startswith(original), "original attempts changed"
        )
        record_analysis(args.run_spec, run, native, panel, contract)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
