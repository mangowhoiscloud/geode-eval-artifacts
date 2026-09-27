"""Read or record X1a admission through the pinned producer's existing contracts.

No dispatch and no external labels, gold, selection freeze, T or tau are read.
--record appends one native analysis-only attempt and creates choice/results.json
and choice/analysis.json; every original attempt and receipt is retained.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REVISION = "2f2b494d605c9306dcf1d94a2394e7576e959ace"
PRIMARY = "x1_admission_admitted_ratio"
ENGINES = ("llm", "jev")
ADMISSION_STATES = {"x1-580a8e039ac4aefb", "x1-f2684c4eaf078047"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def owners(source: Path, phase: Path) -> tuple[Any, Any, Any, Any]:
    git = lambda *args: subprocess.run(  # noqa: E731, S603 - fixed git executable and arguments
        ["/usr/bin/git", "-C", str(source), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    require(git("rev-parse", "HEAD") == REVISION, "requires exact source #2")
    require(not git("status", "--porcelain"), "source #2 checkout is dirty")
    frozen = load(phase / "freeze.json")
    require(frozen["unit"] == "X1a" and frozen["source_revision"] == REVISION, "wrong freeze")
    # Verify local code before importing the installed driver.
    for filename in ("panel_driver.py", "track_common.py", "source_pin.py", "run_guards.py"):
        path = phase.parent / filename
        require(frozen["sha256"].get(str(path)) == sha(path), f"driver hash changed: {filename}")
    sys.path[:0] = [str(source), str(phase.parent)]
    driver = importlib.import_module("panel_driver")
    require(Path(driver.__file__).resolve().parent == phase.parent, "another driver was loaded")
    pinned, revision = driver.tc.pinned_source()
    require(pinned == source and revision == REVISION, "source pin differs")
    panel = importlib.import_module("evals.benchmarks.verdict_panel_runner")
    require(
        Path(panel.__file__).resolve().is_relative_to(source), "another GEODE source was loaded"
    )
    contract = importlib.import_module("scripts.eval.contract")
    verifier = importlib.import_module("evals.benchmarks.decision_verification")
    return driver, panel, contract, verifier


def execution_guard(
    phase: Path, frozen: dict[str, Any], receipt_path: Path | None
) -> dict[str, Any]:
    """Bind existing dispatch/block evidence and the operator's completed process result."""
    if receipt_path is None:
        return {
            "verified": False,
            "reason": "execution exit receipt required; component report only",
        }
    done = load(receipt_path)
    require(
        done.get("exit_code") == 0 and type(done.get("exit_code")) is int,
        "driver did not exit zero",
    )
    require(
        done.get("unit") == "X1a" and done.get("source_revision") == REVISION,
        "execution identity differs",
    )
    require(done.get("freeze_sha256") == sha(phase / "freeze.json"), "execution freeze differs")
    require(done.get("driver_sha256") == frozen["driver_sha256"], "execution driver differs")
    dispatch_path = phase / "dispatch-summary.json"
    dispatch = load(dispatch_path)
    require(
        dispatch.get("stopped") is False and dispatch.get("stop_reason") is None,
        "dispatch did not complete",
    )
    require(
        dispatch.get("planned_calls") == dispatch.get("dispatched_calls") == 4,
        "dispatch matrix incomplete",
    )
    require(dispatch.get("substitutions") == 0, "X1a replacement exceeds 2 percent")
    block_path = phase / "private-receipts" / f"{frozen['run_ids']['choice']}-block.json"
    block = load(block_path)
    require(
        block.get("unit") == "X1a" and block.get("run_id") == frozen["run_ids"]["choice"],
        "block identity differs",
    )
    require(
        block.get("source_revision") == REVISION
        and block.get("freeze_sha256") == sha(phase / "freeze.json"),
        "block source or freeze differs",
    )
    require(
        block.get("lock_mode") == "panel-unit" and block.get("account_matches_g0") is True,
        "execution guards not admitted",
    )
    require(
        block.get("planned_calls") == block.get("dispatched_calls") == 4
        and block.get("stop_reason") is None,
        "block matrix incomplete",
    )
    return {
        "verified": True,
        "process_receipt_sha256": sha(receipt_path),
        "dispatch_summary_sha256": sha(dispatch_path),
        "block_receipt_sha256": sha(block_path),
        "privacy_basis": (
            "exact pinned driver completed with exit 0 after its finally privacy check"
        ),
    }


def reports(
    source: Path, phase: Path, execution_receipt: Path | None = None
) -> tuple[dict[str, Any], Any, Any]:
    driver, panel, contract, verifier = owners(source, phase)
    frozen, _ = driver.preflight("X1a")  # source pin, every input digest, rebuilt cells
    execution = execution_guard(phase, frozen, execution_receipt)
    require(driver.phase_dir("X1a").resolve() == phase, "phase must be installed driver's x1a")
    require(
        (frozen["judgment"], frozen["mode"], frozen["max_concurrency"], frozen["lock_mode"])
        == ("verdict", "latin", 4, "panel-unit"),
        "wrong X1a execution policy",
    )
    require(
        len(frozen["cells"]) == 4
        and frozen["planned_calls"] == 4
        and len(set(frozen["workload_ids"])) == len(frozen["workload_ids"]) == 2
        and set(frozen["workload_ids"]) == ADMISSION_STATES
        and set(frozen["run_ids"]) == {"choice"}
        and all(cell["primitive"] == "choice" for cell in frozen["cells"]),
        "X1a plan must be two states and four Choice-only calls",
    )
    output = {}
    for primitive in ("choice",):
        spec_path = phase / f"run-spec.{primitive}.json"
        spec = contract.validate_run_spec(spec_path)
        require(spec["run_id"] == frozen["run_ids"]["choice"], "spec run identity differs")
        require(spec["study"]["primary_metric"]["name"] == PRIMARY, "wrong primary")
        require(spec["study"]["primary_metric"]["denominator"] == 4, "wrong denominator")
        require(
            re.findall(
                r"X1a analysis entry sha256:([0-9a-f]{64})(?![0-9a-f])",
                spec["study"]["analysis_plan"],
            )
            == [sha(Path(__file__))],
            "analysis entry SHA missing, duplicated or changed",
        )
        require(
            all(
                spec["artifacts"].get(key) == value
                for key, value in {
                    "native_results": "choice/results.json",
                    "attempts": "choice/attempts.jsonl",
                    "analysis": "choice/analysis.json",
                }.items()
            ),
            "spec artifacts must bind the Choice run directory",
        )
        require(spec["reproduction"]["geode"]["revision"] == REVISION, "spec source differs")
        require(
            spec["preregistration"]["status"] == "frozen"
            and spec["preregistration"]["mode"] == "prospective",
            "unfrozen or non-prospective spec",
        )
        run = phase / primitive
        rows = contract.validate_attempts(run / "attempts.jsonl")
        require(
            all(r["change"]["surface"] == "judgment-panel" for r in rows),
            "aggregate already exists",
        )
        require(all(r["run_id"] == spec["run_id"] for r in rows), "run identity mismatch")
        require(
            all(r["selected_for_analysis"] for r in rows),
            "X1a cannot deselect calls: one replacement / 4 exceeds 2%",
        )
        require(len(rows) <= 4, "X1a cannot contain more than its four original attempts")
        frozen_at = datetime.fromisoformat(
            spec["preregistration"]["frozen_at"].replace("Z", "+00:00")
        )
        require(
            all(
                r["timing"]["status"] == "exact"
                and datetime.fromisoformat(r["timing"]["started_at"].replace("Z", "+00:00"))
                >= frozen_at
                for r in rows
            ),
            "attempt predates freeze or lacks exact timing",
        )
        planned = {
            (c["workload_id"], c["engine"]): c
            for c in frozen["cells"]
            if c["primitive"] == primitive
        }
        require(len(planned) == 4, "duplicate frozen cell")
        require(
            set(planned)
            == {(workload, engine) for workload in frozen["workload_ids"] for engine in ENGINES},
            "frozen matrix must contain each state once per engine",
        )
        selected = panel._selected_judgments(run, primitive)
        observed = set()
        stats = {
            e: {
                "planned": 2,
                "admitted": 0,
                "rejected": 0,
                "invalid": 0,
                "strict_admitted": 0,
                "tolerance_only_admitted": 0,
            }
            for e in ENGINES
        }
        for row, evidence in selected:
            key = (evidence["workload_id"], evidence["engine"])
            require(key in planned and key not in observed, "unexpected or duplicate selected cell")
            observed.add(key)
            cell = planned[key]
            require(
                all(evidence[k] == cell[k] for k in ("state_id", "cluster_id", "variant")),
                "cell identity changed",
            )
            engine = evidence["engine"]
            if row["validity"] != "valid":
                stats[engine]["invalid"] += 1
                continue
            receipt = evidence.get("receipt")
            require(isinstance(receipt, dict), "valid attempt lacks its native receipt")
            expected = (
                ("gpt-6-astra", "openai", "subscription")
                if engine == "llm"
                else ("jev-1.13.0", "typesafe", "payg")
            )
            require(
                (receipt["model"], receipt["provider"], receipt["source"]) == expected,
                "route mismatch",
            )
            require(receipt["input_sha256"] == cell["case_sha256"], "input digest mismatch")
            require(
                receipt["question_sha256"]
                == verifier.contract_digests(primitive)["question_sha256"],
                "question digest mismatch",
            )
            require(receipt["contract"] == verifier.CONTRACT_VERSION, "unapproved schema contract")
            require(receipt["sum_tolerance"] == 0.025, "unexpected acceptance tolerance")
            admitted = evidence["status"] == "admitted"
            require(
                admitted == (receipt["accepted"] is True) == (row["outcome"] == "passed"),
                "admission fields disagree",
            )
            if admitted:
                require(
                    receipt["response_model"] == expected[0]
                    # The pinned producer stores its accepted blank provider as null.
                    and receipt.get("response_provider") in (None, expected[1]),
                    "admitted response route mismatch",
                )
                require(
                    evidence["stop_reason"] == ("completed" if engine == "llm" else "end_turn"),
                    "unadmitted response termination",
                )
                require(
                    receipt["raw_answer_retention"] == "complete", "admitted answer not retained"
                )
                raw = receipt["raw_answer"]
                require(
                    hashlib.sha256(raw.encode()).hexdigest() == receipt["raw_answer_sha256"],
                    "native answer digest mismatch",
                )
                decision = verifier.decide_answer(engine, primitive, raw, sum_tolerance=0.025)
                for field in ("verdict", "probabilities", "q", "projected_payload"):
                    require(receipt[field] == decision[field], f"recomputed {field} differs")
                strict = verifier.strict_admission(engine, primitive, raw)
                require(receipt["strict_admitted"] is strict, "strict classification differs")
                stats[engine]["admitted"] += 1
                stats[engine]["strict_admitted" if strict else "tolerance_only_admitted"] += 1
            else:
                require(
                    evidence["status"] == "rejected"
                    and row["failure_class"] == "invalid_judge_output",
                    "invalid rejection class",
                )
                stats[engine]["rejected"] += 1
        missing = sorted(set(planned) - observed)
        measurable = not missing and not any(s["invalid"] for s in stats.values())
        numerator = sum(s["admitted"] for s in stats.values())
        primary = {
            "value": numerator / 4 if measurable else "not-measurable",
            "numerator": numerator if measurable else None,
            "denominator": 4 if measurable else None,
        }
        gate = measurable and numerator == 4
        output[primitive] = {
            "schema": "jev-v3.x1a-admission-summary@1",
            "run_id": spec["run_id"],
            "source_revision": REVISION,
            "source_freeze_sha256": sha(phase / "freeze.json"),
            "source_run_spec_sha256": sha(spec_path),
            "source_attempts_sha256": sha(run / "attempts.jsonl"),
            "primary": primary,
            "engines": stats,
            "missing_selected_cells": missing,
            "component_gate_passed": gate,
            "admission_gate_passed": gate and execution["verified"],
            "execution_guard": execution,
            "analysis_entry_sha256": sha(Path(__file__)),
            "measurable": measurable,
            "scope": (
                "output admission only; no correctness, latency or generalized performance claim"
            ),
            "gate_rule": (
                "all four Choice calls admitted; two fixed states by two engines; "
                "no substitutions; execution guard/privacy receipt also required"
            ),
        }
    return output, panel, contract


def record(phase: Path, output: dict[str, Any], panel: Any, contract: Any) -> None:
    require(
        all(r["execution_guard"]["verified"] for r in output.values()),
        "record requires completed guarded execution",
    )
    # Refuse ordinary repeats before adding the native analysis-only aggregate.
    for primitive in output:
        run = phase / primitive
        for name in ("results.json", "analysis.json"):
            require(not (run / name).exists(), f"{primitive}/{name} already exists")
    for primitive, report in output.items():
        run = phase / primitive
        original = (run / "attempts.jsonl").read_bytes()
        panel._record_aggregate(
            run,
            "results.json",
            report,
            failure_class=None if report["measurable"] else "incomplete_or_invalid_admission",
            description="Frozen X1a output-admission aggregation; zero model dispatches.",
            expected_effect=(
                "Report the frozen 4-cell admitted ratio and operational admission gate."
            ),
            observed=(
                "Every planned selected call is valid.",
                "A planned call is missing or selected invalid.",
            ),
        )
        require(
            (run / "attempts.jsonl").read_bytes().startswith(original), "original attempts changed"
        )
        rows = contract.validate_attempts(run / "attempts.jsonl")
        selected = [r for r in rows if r["selected_for_analysis"]]
        refs = {
            json.dumps(ref, sort_keys=True): ref for row in selected for ref in row["evidence_refs"]
        }
        analysis = {
            "schema_id": "geode.eval-analysis@1",
            "schema_version": 1,
            "run_id": report["run_id"],
            "analyzed_at": datetime.now(UTC).isoformat(),
            "run_spec_sha256": report["source_run_spec_sha256"],
            "attempts_sha256": sha(run / "attempts.jsonl"),
            "selected_attempt_ids": [r["attempt_id"] for r in selected],
            "answer": "X1a output admission gate passed."
            if report["admission_gate_passed"]
            else "X1a output admission gate did not pass.",
            "metrics": [
                panel._bound_row(
                    PRIMARY, report["primary"], "/primary", unit="ratio", source_ref="results.json"
                )
            ],
            "decision": {
                "outcome": "diagnostic-only",
                "hypothesis_status": (
                    "supported" if report["admission_gate_passed"] else "not-supported"
                )
                if report["measurable"]
                else "invalidated",
                "rationale": report["gate_rule"],
            },
            "limitations": [
                report["scope"],
                "Operational execution-guard and exact-byte privacy checks are separate gates.",
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument(
        "--phase", required=True, type=Path, help="installed P driver's x1a directory"
    )
    parser.add_argument("--record", action="store_true")
    parser.add_argument(
        "--execution-receipt",
        type=Path,
        help="operator-recorded completed driver exit tied to freeze and source",
    )
    args = parser.parse_args(argv)
    phase = args.phase.resolve()
    output, panel, contract = reports(args.source.resolve(), phase, args.execution_receipt)
    if args.record:
        record(phase, output, panel, contract)
    print(json.dumps(output, ensure_ascii=False, indent=2))
    if args.execution_receipt is None:
        return 2
    return 0 if all(r["admission_gate_passed"] for r in output.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
