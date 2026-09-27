"""Offline U0b admission sidecars; no held-out grades and no model calls.

Install beside the private drivers before U0b freeze and bind this file's SHA
in the run-spec. Run with --record after both G and P phases. An analysis-only
aggregate attempt is timed here; selector execution timestamps are not invented.
Incomplete execution is retained as not-measurable and never freezes a tolerance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PRIMARY = "score_admission_valid_selection_ratio"
SELECTORS = {
    "astra_pointwise": ("pointwise", "llm"),
    "jev_pointwise": ("pointwise", "jev"),
    "astra_listwise": ("listwise", None),
}
BOUNDS = {"sum_tolerance": 0.025, "score_tolerance": 0.05}
OUTPUTS = (
    "results.json",
    "attempts.jsonl",
    "analysis.json",
    "score-tolerance-freeze.json",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> Any:
    from scripts.eval.contract import _strict_json_loads

    return _strict_json_loads(path.read_text(), label=path.name)


def jsonl(path: Path) -> list[dict[str, Any]]:
    from scripts.eval.contract import _strict_json_loads

    return [
        _strict_json_loads(line, label=f"{path.name}:{n}")
        for n, line in enumerate(path.read_text().splitlines(), 1)
        if line.strip()
    ]


def summarize(
    spec: dict[str, Any],
    frozen: dict[str, Any],
    pools: list[Any],
    records: list[dict[str, Any]],
    execution_errors: list[str],
) -> dict[str, Any]:
    """Admission uses selected order.valid, independently checked against its receipts.

    Only the generated natural pool has grades inspected, for the preregistered
    discriminativeness diagnostic. Controlled pool grades are never accessed.
    """
    from evals.benchmarks import score_selection as ss

    ids = spec["reproduction"]["execution"]["ordered_workload_ids"]
    if (
        spec["study"]["primary_metric"]["name"] != PRIMARY
        or spec["study"]["primary_metric"]["denominator"] != 18
        or len(ids) != 3
        or len(set(ids)) != 3
        or [p.pool_id for p in pools] != ids
        or frozen["workload_ids"] != ids
        or frozen["tolerances"] != BOUNDS
    ):
        raise ValueError("U0b needs the frozen three pools, 18 calls and 0.025/0.05 bounds")
    natural = [pool for pool in pools if pool.kind == "natural"]
    if len(natural) != 1 or sum(p.kind == "controlled" for p in pools) != 2:
        raise ValueError("U0b needs exactly two controlled pools and one natural pool")
    errors = list(execution_errors)
    by_id = {r.get("pool_id"): r for r in records}
    if len(by_id) != len(records) or set(by_id) != set(ids):
        errors.append("incomplete_or_duplicate_planned_pools")
    cells: list[dict[str, Any]] = []
    deviations: list[float] = []
    for pool in pools:
        record = by_id.get(pool.pool_id)
        if record is None:
            continue
        if (
            record.get("schema") != ss.RECORD_SCHEMA
            or record.get("frozen_pool_sha256") != ss.frozen_pool_sha256(pool)
            or record.get("kind") != pool.kind
        ):
            raise ValueError(f"{pool.pool_id}: dispatch record identity differs from frozen pool")
        selectors = record.get("selectors", {})
        if set(selectors) != set(SELECTORS):
            errors.append(f"{pool.pool_id}:incomplete_selectors")
        cids = [c.candidate_id for c in pool.candidates]
        for name, (kind, engine) in SELECTORS.items():
            entry = selectors.get(name)
            if entry is None:
                continue
            if (entry.get("type"), entry.get("engine")) != (kind, engine):
                raise ValueError(f"{pool.pool_id}/{name}: selector identity changed")
            if name == "jev_pointwise" and entry.get("tolerances") != BOUNDS:
                raise ValueError("Jev selector bounds differ from the frozen admission ceiling")
            try:
                orders = ss._check_orders(entry, cids, f"{pool.pool_id}/{name}")
            except ValueError as error:
                errors.append(str(error))
                continue
            for order in ss.ORDERS:
                row = orders[order]
                valid = row.get("valid")
                if type(valid) is not bool or row.get("selector_calls") != 1:
                    raise ValueError("selected order lacks a boolean validity or one-call identity")
                # A single replacement is already > 2% of this 18-call admission.
                if row.get("replaced_attempts"):
                    errors.append("substitution_rate_exceeded")
                if valid:
                    if row.get("failure") is not None or row.get("judge_error"):
                        raise ValueError("valid selection contradicts its failure fields")
                    if row.get("winner_id") not in cids:
                        raise ValueError("valid selection has no frozen candidate winner")
                    if kind == "pointwise":
                        receipt = row.get("receipt")
                        if not isinstance(receipt, dict) or receipt.get("accepted") is not True:
                            raise ValueError("valid pointwise selection lacks an admitted receipt")
                        scores = ss._fractions(row.get("scores"), cids, name)
                        winner, _ = ss.select_by_score(pool.pool_id, scores)
                        presented = cids if order == "forward" else cids[::-1]
                        if winner != row["winner_id"] or receipt.get(
                            "winner_index"
                        ) != presented.index(winner):
                            raise ValueError("pointwise argmax projection mismatch")
                if name == "jev_pointwise":
                    receipt = row.get("receipt")
                    value = ss._expectation_deviation(receipt)
                    observed = row.get("expectation_deviation")
                    if value is None:
                        if observed is not None:
                            raise ValueError("reported Score deviation has no raw-answer evidence")
                    elif (
                        type(observed) not in (int, float)
                        or not math.isfinite(observed)
                        or observed != value
                    ):
                        raise ValueError("reported Score deviation differs from pinned raw parser")
                    else:
                        deviations.append(value)
                    if valid and (
                        receipt.get("sum_tolerance") != BOUNDS["sum_tolerance"]
                        or receipt.get("score_tolerance") != BOUNDS["score_tolerance"]
                    ):
                        raise ValueError("Jev receipt bounds differ from its selector")
                cells.append(
                    {
                        "pool_id": pool.pool_id,
                        "selector": name,
                        "order": order,
                        "valid": valid,
                        "failure": row.get("failure"),
                    }
                )
    if len(cells) != 18:
        errors.append("incomplete_planned_orders")
    pool = natural[0]
    complete = len(pool.candidates) == 4 and pool.provenance.get("complete") is True
    if not complete:
        errors.append("incomplete_natural_generation")
    non_discriminative = len({candidate.grade for candidate in pool.candidates}) == 1
    errors = sorted(set(errors))
    valid_count = sum(cell["valid"] for cell in cells)
    metric = {
        "name": PRIMARY,
        "value": "not-measurable" if errors else valid_count / 18,
        "numerator": None if errors else valid_count,
        "denominator": None if errors else 18,
    }
    maximum = max(deviations) if deviations else None
    score = {
        "orders_measured": len(deviations),
        "max_abs_deviation": maximum,
        "tolerance_rule": ss.TOLERANCE_RULE,
        "tolerance": ss.score_expectation_tolerance(maximum) if maximum is not None else None,
    }
    return {
        "schema_id": "jev-v3.u0b-admission@1",
        "run_id": spec["run_id"],
        "primary_metric": metric,
        "errors": errors,
        "orders": cells,
        "observed_valid_selections": valid_count,
        "planned_selector_calls": 18,
        "score_expectation": score,
        "natural": {
            "pool_id": pool.pool_id,
            "complete": complete,
            "non_discriminative": {
                "value": float(non_discriminative),
                "numerator": int(non_discriminative),
                "denominator": 1,
            },
            "u5_descriptive_only": non_discriminative,
        },
        "tolerance_freeze_ready": not errors and valid_count == 18 and len(deviations) == 6,
    }


def record_bundle(
    directory: Path,
    spec: dict[str, Any],
    report: dict[str, Any],
    evidence_paths: list[Path],
) -> None:
    """Write new sidecars, validate their existing v1 contract, then freeze the rule."""
    import track_common as tc
    from scripts.eval.contract import validate_run_bundle

    for name in OUTPUTS:
        if (directory / name).exists():
            raise FileExistsError(f"preserve existing {name}; do not rerun this lineage")
    report = {
        **report,
        "source_revision": spec["reproduction"]["geode"]["revision"],
        "run_spec_sha256": sha(directory / "run-spec.json"),
        "analysis_entry_sha256": sha(Path(__file__)),
        "source_sha256": {str(p.relative_to(directory)): sha(p) for p in evidence_paths},
    }
    tc.write_new(directory / "results.json", report)
    refs = [
        {
            "kind": "native-result",
            "path": "results.json",
            "sha256": sha(directory / "results.json"),
        }
    ]
    refs += [
        {"kind": "other", "path": str(p.relative_to(directory)), "sha256": sha(p)}
        for p in evidence_paths
    ]
    at = tc.now()
    invalid = bool(report["errors"])
    passed = not invalid and report["observed_valid_selections"] == 18
    attempt_id = f"{spec['run_id']}-admission-analysis"
    attempt = {
        "schema_id": "geode.eval-attempt@1",
        "schema_version": 1,
        "run_id": spec["run_id"],
        "attempt_id": attempt_id,
        "parent_attempt_id": None,
        "sequence": 0,
        "timing": {
            "status": "exact",
            "started_at": at,
            "finished_at": at,
            "source_ref": None,
        },
        "validity": "invalid" if invalid else "valid",
        "outcome": "unknown" if invalid else "passed" if passed else "failed",
        "change": {
            "surface": "analysis-only",
            "description": "Grade-free U0b aggregate of retained selector records; "
            "no model dispatch. "
            "This timestamp measures aggregation, not selector execution.",
        },
        "expected_effect": "Measure admitted selector outputs over all 18 planned calls.",
        "observed_result": f"Observed {report['observed_valid_selections']}/18 valid outputs; "
        f"invalidation reasons: {report['errors']}.",
        "failure_class": report["errors"][0]
        if invalid
        else None
        if passed
        else "judgment_output_invalid",
        "error_ref": None,
        "evidence_refs": refs,
        "selected_for_analysis": True,
    }
    tc.write_new(directory / "attempts.jsonl", json.dumps(attempt, ensure_ascii=False) + "\n")
    primary = report["primary_metric"]
    analysis = {
        "schema_id": "geode.eval-analysis@1",
        "schema_version": 1,
        "run_id": spec["run_id"],
        "analyzed_at": tc.now(),
        "run_spec_sha256": sha(directory / "run-spec.json"),
        "attempts_sha256": sha(directory / "attempts.jsonl"),
        "selected_attempt_ids": [attempt_id],
        "answer": "U0b selector contracts admitted 18/18 outputs."
        if passed
        else "U0b admission did not establish all 18 admissible selector outputs.",
        "metrics": [
            {
                **primary,
                "unit": "ratio",
                "source_ref": "results.json",
                "source_locator": {
                    k: f"/primary_metric/{k}" for k in ("value", "numerator", "denominator")
                },
            }
        ],
        "decision": {
            "outcome": "diagnostic-only",
            "hypothesis_status": "invalidated"
            if invalid
            else "supported"
            if passed
            else "not-supported",
            "rationale": "Apply the frozen 18-output admission; "
            "no correctness or model superiority claim.",
        },
        "limitations": [
            "Controlled test grades remain sealed; oracle-best selection is not measured.",
            "The single natural pool is only a discriminativeness diagnostic.",
            "Aggregate attempt timing is analysis-only; "
            "original dispatch timing stays in native evidence.",
            "Admission pass and sufficient Score deviation coverage are separately reported.",
        ],
        "evidence_refs": refs,
    }
    tc.write_new(directory / "analysis.json", analysis)
    validate_run_bundle(directory / "run-spec.json")
    if report["tolerance_freeze_ready"]:
        tc.write_new(
            directory / "score-tolerance-freeze.json",
            {
                "schema_id": "jev-v3.score-tolerance-freeze@1",
                "run_id": spec["run_id"],
                "frozen_at": tc.now(),
                "sum_tolerance": 0.025,
                "score_tolerance": report["score_expectation"]["tolerance"],
                "score_expectation": report["score_expectation"],
                "u0b_max_abs_deviation": report["score_expectation"]["max_abs_deviation"],
                "u5_descriptive_only": report["natural"]["u5_descriptive_only"],
                "source_revision": spec["reproduction"]["geode"]["revision"],
                "sha256": {
                    name: sha(directory / name)
                    for name in (
                        "run-spec.json",
                        "freeze.json",
                        "dispatch-records.jsonl",
                        "results.json",
                        "attempts.jsonl",
                        "analysis.json",
                    )
                },
            },
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", action="store_true", help="write new immutable sidecars")
    args = parser.parse_args(argv)
    import track_common as tc

    tc.pinned_source()
    import score_driver
    from scripts.eval.contract import validate_run_spec

    directory = score_driver.phase_dir("U0b")
    frozen, pools = score_driver.preflight("U0b")
    spec = validate_run_spec(directory / "run-spec.json")
    token = f"U0b analysis entry sha256 {sha(Path(__file__))}"
    if token not in spec["reproduction"]["harness"]["source"]:
        raise ValueError("U0b analysis entry is not bound to the frozen run-spec")
    evidence = [directory / "freeze.json"]
    records_path = directory / "dispatch-records.jsonl"
    records = jsonl(records_path) if records_path.exists() else []
    errors = []
    if records_path.exists():
        evidence.append(records_path)
    for filename in ("timings.json", "tolerance-check.json"):
        path = directory / filename
        if path.exists():
            evidence.append(path)
            if filename == "tolerance-check.json" and read(path).get("exit_code") != 0:
                errors.append("tolerance_check_failed")
        else:
            errors.append(f"missing_{filename}")
    receipt_path = directory / "private-receipts" / f"{spec['run_id']}-block.json"
    if receipt_path.exists():
        receipt = read(receipt_path)
        evidence.append(receipt_path)
        if (
            receipt.get("run_id") != spec["run_id"]
            or receipt.get("unit") != "U0b"
            or receipt.get("source_revision") != frozen["source_revision"]
            or receipt.get("freeze_sha256") != sha(directory / "freeze.json")
            or receipt.get("planned_calls") != 18
            or receipt.get("records") != 3
            or receipt.get("tolerances") != BOUNDS
            or receipt.get("stop_reason") is not None
        ):
            errors.append("execution_block_not_complete")
    else:
        errors.append("missing_execution_block")
    gen = HERE / "u0b-pool"
    generation = read(gen / "freeze.json")
    tc.check_bound(generation["sha256"])
    if (
        generation["source_revision"] != frozen["source_revision"]
        or sha(gen / "run-spec.json") != sha(directory / "run-spec.json")
        or generation["best_of"] != 4
        or len(generation["tasks"]) != 1
        or generation["tasks"][0]["pool_id"]
        != next(p.pool_id for p in pools if p.kind == "natural")
        or str((gen / "pools.natural.jsonl").resolve()) not in frozen["sha256"]
    ):
        raise ValueError("natural pool is not bound to the same U0b generation freeze")
    gen_receipt_path = gen / "private-receipts" / f"{spec['run_id']}-block.json"
    if not gen_receipt_path.exists():
        errors.append("missing_generation_block")
    else:
        receipt = read(gen_receipt_path)
        if (
            receipt.get("run_id") != spec["run_id"]
            or receipt.get("unit") != "U0b-gen"
            or receipt.get("source_revision") != frozen["source_revision"]
            or receipt.get("freeze_sha256") != sha(gen / "freeze.json")
            or receipt.get("planned_tasks") != 1
            or receipt.get("frozen_pools") != 1
            or receipt.get("stop_reason") is not None
        ):
            errors.append("generation_block_not_complete")
    # Driver block receipts precede quota/secret checks in finally. Require the
    # coordinator's subprocess exit receipt for both full execute invocations.
    for phase, unit, phase_freeze in ((directory, "U0b", frozen), (gen, "U0b-gen", generation)):
        path = phase / "execution-receipt.json"
        if not path.exists():
            errors.append(f"{unit}:missing_execution_exit_receipt")
            continue
        exit_receipt = read(path)
        if (
            exit_receipt.get("unit") != unit
            or exit_receipt.get("source_revision") != phase_freeze["source_revision"]
            or exit_receipt.get("freeze_sha256") != sha(phase / "freeze.json")
            or exit_receipt.get("driver_sha256") != phase_freeze["driver_sha256"]
            or type(exit_receipt.get("exit_code")) is not int
            or exit_receipt["exit_code"] != 0
        ):
            errors.append(f"{unit}:execution_not_successfully_closed")
        if phase == directory:
            evidence.append(path)
    report = summarize(spec, frozen, pools, records, errors)
    report["generation_evidence_sha256"] = {
        name: sha(gen / name)
        for name in (
            "freeze.json",
            "run-spec.json",
            "pools.natural.jsonl",
            "generation-usage.jsonl",
        )
    }
    if (gen / "execution-receipt.json").exists():
        report["generation_evidence_sha256"]["execution-receipt.json"] = sha(
            gen / "execution-receipt.json"
        )
    if gen_receipt_path.exists():
        report["generation_evidence_sha256"]["private-receipts/block.json"] = sha(gen_receipt_path)
    if args.record:
        record_bundle(directory, spec, report, evidence)
    print(
        json.dumps(
            {
                "primary": report["primary_metric"],
                "errors": report["errors"],
                "score_expectation": report["score_expectation"],
                "tolerance_freeze_ready": report["tolerance_freeze_ready"],
            },
            indent=2,
        )
    )
    return 0 if report["tolerance_freeze_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
