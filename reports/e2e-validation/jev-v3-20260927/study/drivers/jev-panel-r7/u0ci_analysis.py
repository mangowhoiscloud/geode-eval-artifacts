"""Offline U0c-i admission connection to the pinned intent report and v1 analysis.

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

REVISION = "2f2b494d605c9306dcf1d94a2394e7576e959ace"
UNIT = "U0c-i"
PRIMARY = "intent_panel_admission_admitted_ratio"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def reports(source: Path, phase: Path, meta: Path, execution_receipt: Path) -> tuple[Any, Any, Any]:
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
        len(workloads) == 4 and len(frozen["cells"]) == 8,
        "admission needs four families/eight calls",
    )
    spec_path = phase / "run-spec.choice.json"
    spec = contract.validate_run_spec(spec_path)
    require(
        spec["study"]["primary_metric"]["name"] == PRIMARY
        and spec["study"]["primary_metric"]["denominator"] == 8,
        "wrong admission metric",
    )
    for key, value in {
        "native_results": "choice/intent-results.json",
        "attempts": "choice/attempts.jsonl",
        "analysis": "choice/analysis.json",
    }.items():
        require(spec["artifacts"][key] == value, f"run-spec artifact path differs: {key}")
    panel_path = Path(frozen["states"])
    require(
        f"i-panel admission sha256:{sha(panel_path)}"
        in spec["reproduction"]["environment"]["initial_state_ref"],
        "panel SHA not registered",
    )
    plan = spec["study"]["analysis_plan"]
    require(f"i-panel meta sha256:{sha(meta)}" in plan, "meta SHA not registered")
    require(
        f"U0c-i analysis entry sha256:{sha(Path(__file__))}" in plan,
        "analysis entry SHA not registered",
    )
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
    require(
        dispatch.get("stopped") is False
        and dispatch.get("stop_reason") is None
        and dispatch.get("planned_calls") == dispatch.get("dispatched_calls") == 8
        and dispatch.get("substitutions") == 0,
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
        and block.get("planned_calls") == block.get("dispatched_calls") == 8
        and block.get("stop_reason") is None,
        "execution guards not admitted",
    )
    # Account identity belongs to the hash-bound installed guard; no account is hard-coded here.
    run = phase / "choice"
    rows = contract.validate_attempts(run / "attempts.jsonl")
    require(
        len(rows) == 8
        and all(
            row["change"]["surface"] == "judgment-panel"
            and row["run_id"] == spec["run_id"]
            and row["selected_for_analysis"]
            for row in rows
        ),
        "expected eight original selected attempts, no aggregate/replacement",
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
            check_admitted(handoff, states[key[0]], engine, receipt, evidence, expected)
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
    report["admission_provenance"] = {
        "source_revision": REVISION,
        "run_spec_sha256": sha(spec_path),
        "source_attempts_sha256": sha(run / "attempts.jsonl"),
        "freeze_sha256": sha(phase / "freeze.json"),
        "panel_sha256": sha(panel_path),
        "meta_sha256": sha(meta),
        "analysis_entry_sha256": sha(Path(__file__)),
        "execution_receipt_sha256": sha(execution_receipt),
        "dispatch_summary_sha256": sha(dispatch_path),
        "block_receipt_sha256": sha(block_path),
        "strict_jev_sum_tolerance": 1e-5,
        "privacy_basis": "Pinned driver exit zero after its finally privacy check; "
        "not public-release approval",
    }
    return report, panel, contract


def check_admitted(
    handoff: Any,
    state: dict[str, Any],
    engine: str,
    receipt: dict[str, Any],
    evidence: dict[str, Any],
    expected: tuple[str, ...],
) -> None:
    """Recompute public questions, strict Jev primitives, and source-span projection offline."""
    from core.llm.adapters.base import AdapterCallResult, UsageSummary
    from evals.benchmarks.decision_handoff_runtime import inbox_request

    require(
        receipt.get("response_model") == expected[0]
        and receipt.get("response_provider") in (None, expected[1]),
        "response route differs",
    )
    require(
        evidence["stop_reason"] == ("completed" if engine == "llm" else "end_turn"),
        "response termination differs",
    )
    require(receipt["raw_answer_retention"] == "complete", "admitted raw answer not retained")
    raw = receipt["raw_answer"]
    require(
        hashlib.sha256(raw.encode()).hexdigest() == receipt["raw_answer_sha256"], "raw SHA differs"
    )
    items = handoff.inbox_family_items(state)
    tool = handoff.DecisionHandoffTool(
        inbox_request(items), "a", requests={item["id"]: item["request"] for item in items}
    )
    payload = tool._payload()
    require(
        receipt["question_sha256"] == handoff._canonical_sha256(payload["questions"])
        and receipt["source_sha256"] == tool._source_sha256,
        "helper question/source hash differs",
    )
    if engine == "jev":
        # This is the same strict parser used by the pinned E2E helper: sum tolerance 1e-5.
        primitives = handoff.parse_choice_answers(raw, payload["questions"])
        require(primitives == receipt["primitives"], "strict Jev primitive admission differs")
        raw = json.dumps({key: value["choice"] for key, value in primitives.items()})
    else:
        require(receipt["primitives"] is None, "Astra must not have native Jev primitives")
    decided = tool._admit(
        AdapterCallResult(
            text=raw, usage=UsageSummary(), stop_reason="completed", response_model="gpt-6-astra"
        ),
        payload,
    )
    require(decided["items"] == receipt["items"], "helper item/source-span projection differs")


def record(phase: Path, report: dict[str, Any], panel: Any, contract: Any) -> None:
    run = phase / "choice"
    for name in (panel.INTENT_RESULTS, "analysis.json"):
        require(not (run / name).exists(), f"{name} already exists; preserve lineage")
    original = (run / "attempts.jsonl").read_bytes()
    panel.record_intent_aggregate(run, report)
    require((run / "attempts.jsonl").read_bytes().startswith(original), "original attempts changed")
    rows = contract.validate_attempts(run / "attempts.jsonl")
    selected = [row for row in rows if row["selected_for_analysis"]]
    refs = {
        json.dumps(ref, sort_keys=True): ref for row in selected for ref in row["evidence_refs"]
    }
    admission = report["admission"]
    passed = (
        admission["numerator"] == admission["denominator"] == 8
        and admission["decision"] == "supported"
    )
    analysis = {
        "schema_id": "geode.eval-analysis@1",
        "schema_version": 1,
        "run_id": rows[0]["run_id"],
        "analyzed_at": datetime.now(UTC).isoformat(),
        "run_spec_sha256": sha(phase / "run-spec.choice.json"),
        "attempts_sha256": sha(run / "attempts.jsonl"),
        "selected_attempt_ids": [row["attempt_id"] for row in selected],
        "answer": "U0c-i admitted all eight planned helper responses."
        if passed
        else "U0c-i did not admit all eight planned helper responses.",
        "metrics": panel.intent_metric_rows(report, primary=PRIMARY),
        "decision": {
            "outcome": "diagnostic-only",
            "hypothesis_status": admission["decision"],
            "rationale": "Four frozen families, both engines; admission requires eight admitted "
            "responses and verified execution closure.",
        },
        "limitations": [
            "Admission is schema/route completion, "
            "not perfect helper accuracy or an E2E root result.",
            "Four author-visible families support a diagnostic only, "
            "not generalization or a latency claim.",
            "Original calls remain selected; the extra attempt is analysis-only, "
            "with no model dispatch.",
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
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args(argv)
    phase = args.phase.resolve()
    report, panel, contract = reports(
        args.source.resolve(), phase, args.meta.resolve(), args.execution_receipt.resolve()
    )
    if args.record:
        record(phase, report, panel, contract)
    print(json.dumps({"admission": report["admission"], "engines": report["engines"]}, indent=2))
    return 0 if report["admission"]["decision"] == "supported" else 1


if __name__ == "__main__":
    raise SystemExit(main())
