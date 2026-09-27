"""Private offline U4/U5p/U5s/X2 bridge to the pinned native Score and v1 owners.

Install before prospective freeze. Bind this SHA and the explicit
bootstrap_manifest_sha256:<hex> in analysis_plan. No model path is imported or
executed here. --unsealed-reviewed is required before loading U4/X2 grade files.
Raw dispatch/payload files remain in place; only derived sidecars are created.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
TOLERANCE_SOURCE = "2f2b494d605c9306dcf1d94a2394e7576e959ace"
METRICS = {
    "U4": ("score_ctl_top1_delta", 80),
    "U5p": ("natural_pool_complete_ratio", 12),
    "U5s": ("score_nat_top1_delta", None),
    "X2": ("x2_score_top1_delta", 240),
}
SELECTORS = ("astra_pointwise", "jev_pointwise", "astra_listwise")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> Any:
    from scripts.eval.contract import _strict_json_loads

    return _strict_json_loads(path.read_text(), label=path.name)


def rows(path: Path) -> list[dict[str, Any]]:
    from scripts.eval.contract import _strict_json_loads

    return [
        _strict_json_loads(line, label=f"{path.name}:{n}")
        for n, line in enumerate(path.read_text().splitlines(), 1)
        if line.strip()
    ]


def declared_digests(document: Any) -> set[str]:
    """Digest references only; never discover or open a referenced file."""
    return set(re.findall(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", json.dumps(document)))


def tolerance_authority(path: Path) -> dict[str, Any]:
    """Consume only the existing U0b authority, never fit bounds on main/external data."""
    from scripts.eval.contract import validate_run_bundle

    document = read(path)
    if (
        document.get("schema_id") != "jev-v3.score-tolerance-freeze@1"
        or document.get("source_revision") != TOLERANCE_SOURCE
    ):
        raise ValueError("Score tolerance must come from a source #2 U0b admission")
    expected = {
        "run-spec.json",
        "freeze.json",
        "dispatch-records.jsonl",
        "results.json",
        "attempts.jsonl",
        "analysis.json",
    }
    if set(document.get("sha256", {})) != expected:
        raise ValueError("U0b tolerance authority lacks its complete evidence digests")
    for name, digest in document["sha256"].items():
        if sha(path.parent / name) != digest:
            raise ValueError("U0b tolerance authority evidence changed")
    validate_run_bundle(path.parent / "run-spec.json")
    result = read(path.parent / "results.json")
    if (
        result.get("tolerance_freeze_ready") is not True
        or document.get("sum_tolerance") != 0.025
        or document.get("score_tolerance") != result["score_expectation"]["tolerance"]
        or document.get("u5_descriptive_only") != result["natural"]["u5_descriptive_only"]
    ):
        raise ValueError("U0b did not admit this tolerance or natural-pool diagnostic")
    return document


def metric(
    unit: str, numerator: int | float, denominator: int, errors: list[str]
) -> dict[str, Any]:
    return {
        "name": METRICS[unit][0],
        "value": "not-measurable" if errors or not denominator else numerator / denominator,
        "numerator": None if errors or not denominator else numerator,
        "denominator": None if errors or not denominator else denominator,
    }


def check_spec(unit: str, spec: dict[str, Any], manifest: Path) -> str:
    from track_common import pinned_source

    name, count = METRICS[unit]
    primary = spec["study"]["primary_metric"]
    ids = spec["reproduction"]["execution"]["ordered_workload_ids"]
    if primary["name"] != name or primary["denominator"] != len(ids):
        raise ValueError("primary metric/denominator differs from the ordered workloads")
    if count is not None and len(ids) != count:
        raise ValueError(f"{unit}: registered count is {count}")
    _, revision = pinned_source()
    if spec["reproduction"]["geode"]["revision"] != revision:
        raise ValueError("Score main analysis differs from the run-folder source pin")
    plan = spec["study"]["analysis_plan"]
    matches = re.findall(r"bootstrap_manifest_sha256:([0-9a-f]{64})(?![0-9a-f])", plan)
    digest = sha(manifest)
    if matches != [digest] or sha(Path(__file__)) not in plan:
        raise ValueError("freeze the unique bootstrap manifest and analysis entry SHA before calls")
    return digest


def execution_evidence(
    directory: Path, unit: str, frozen: dict[str, Any], *, allowed_exit: tuple[int, ...] = (0,)
) -> tuple[list[str], list[Path]]:
    """A block receipt precedes finally; require the coordinator's actual subprocess exit too."""
    paths = [directory / "freeze.json"]
    errors = []
    common = {
        "unit": unit,
        "source_revision": frozen["source_revision"],
        "freeze_sha256": sha(directory / "freeze.json"),
    }
    for path, fields in (
        (
            directory / "execution-receipt.json",
            {**common, "driver_sha256": frozen["driver_sha256"]},
        ),
        (
            directory / "private-receipts" / f"{frozen['run_id']}-block.json",
            {**common, "run_id": frozen["run_id"], "stop_reason": None},
        ),
    ):
        if not path.exists():
            errors.append(f"missing_{path.name}")
            continue
        paths.append(path)
        receipt = read(path)
        if any(receipt.get(k) != v for k, v in fields.items()):
            errors.append(f"mismatched_{path.name}")
        if path.name == "execution-receipt.json" and (
            type(receipt.get("exit_code")) is not int or receipt["exit_code"] not in allowed_exit
        ):
            errors.append("execute_not_successfully_closed")
        if path.name != "execution-receipt.json":
            if unit.endswith("-gen"):
                if receipt.get("planned_tasks") != len(frozen["tasks"]):
                    errors.append("generation_plan_mismatch")
            elif (
                receipt.get("planned_calls") != len(frozen["cells"])
                or receipt.get("records") != len(frozen["workload_ids"])
                or receipt.get("tolerances") != frozen["tolerances"]
            ):
                errors.append("selection_matrix_not_complete")
    return errors, paths


def interval(outcomes: list[dict[str, Any]], manifest_sha: str, name: str) -> dict[str, Any]:
    from evals.benchmarks.decision_metrics import bootstrap_seed, cluster_bootstrap

    clusters: dict[str, list[Any]] = defaultdict(list)
    for row in outcomes:
        if not isinstance(row.get("cluster_id"), str) or not row["cluster_id"]:
            raise ValueError(
                "source cluster identity is required; pools are not independent replicas"
            )
        clusters[row["cluster_id"]].append(row)

    def delta(sample: list[Any]) -> float | None:
        return (
            sum(
                row["selectors"]["jev_pointwise"]["oracle_best_value"]
                - row["selectors"]["astra_pointwise"]["oracle_best_value"]
                for row in sample
            )
            / len(sample)
            if sample
            else None
        )

    return cluster_bootstrap(clusters, delta, seed=bootstrap_seed(manifest_sha, name)).as_dict()


def summarize_score(
    unit: str,
    spec: dict[str, Any],
    frozen: dict[str, Any],
    pools: list[Any],
    records: list[dict[str, Any]],
    errors: list[str],
    manifest_sha: str,
    *,
    graded: dict[str, Any] | None = None,
    aliases: dict[str, str] | None = None,
) -> dict[str, Any]:
    from evals.benchmarks import score_selection as ss

    errors = list(errors)
    ids = spec["reproduction"]["execution"]["ordered_workload_ids"]
    if [p.pool_id for p in pools] != ids or frozen["workload_ids"] != ids:
        raise ValueError("dispatched pools differ from the frozen workload order")
    if len(records) != len(ids) or {r.get("pool_id") for r in records} != set(ids):
        errors.append("incomplete_or_duplicate_dispatch")
    by_id = {p.pool_id: p for p in pools}
    replaced = 0
    for record in records:
        entries = record.get("selectors", {})
        pool = by_id.get(record.get("pool_id"))
        if pool is None:
            continue
        if set(entries) != set(SELECTORS):
            errors.append("missing_selector")
        for name, entry in entries.items():
            expected = (
                ("listwise", None)
                if name == "astra_listwise"
                else ("pointwise", "jev" if name == "jev_pointwise" else "llm")
            )
            if (entry.get("type"), entry.get("engine")) != expected:
                raise ValueError("selector identity changed")
            if name == "jev_pointwise" and entry.get("tolerances") != frozen["tolerances"]:
                raise ValueError("Jev bounds differ from the frozen selector")
            if set(entry.get("orders", {})) != set(ss.ORDERS):
                errors.append("missing_order")
            for order, row in entry.get("orders", {}).items():
                replacement = row.get("replaced_attempts") or []
                replaced += len(replacement)
                if len(replacement) > 1:
                    errors.append("replacement_more_than_once")
                if row.get("failure") in ss.INFRASTRUCTURE_FAILURES:
                    errors.append("selected_infrastructure_failure")
                if type(row.get("valid")) is not bool or row.get("selector_calls") != 1:
                    errors.append("missing_selection_observation")
                if row.get("valid") and (
                    row.get("failure") is not None
                    or row.get("judge_error")
                    or (name != "astra_listwise" and not (row.get("receipt") or {}).get("accepted"))
                ):
                    errors.append("validity_receipt_contradiction")
                if row.get("valid") and name != "astra_listwise":
                    cids = [c.candidate_id for c in pool.candidates]
                    presented = cids if order == "forward" else cids[::-1]
                    receipt = row.get("receipt") or {}
                    scores = ss._fractions(row.get("scores"), cids, name)
                    winner, _ = ss.select_by_score(pool.pool_id, scores)
                    if (
                        row.get("winner_id") != winner
                        or receipt.get("winner_index") != presented.index(winner)
                        or receipt.get("scores")
                        != {f"c{i}": row["scores"][cid] for i, cid in enumerate(presented)}
                    ):
                        errors.append("receipt_score_projection_mismatch")
                    if name == "jev_pointwise" and any(
                        receipt.get(k) != v for k, v in frozen["tolerances"].items()
                    ):
                        errors.append("receipt_tolerance_mismatch")
    if replaced / (len(ids) * 6) > 0.02:
        errors.append("substitution_rate_exceeded")
    if unit == "U5s" and any(
        p.kind != "natural" or len(p.candidates) != 4 or p.provenance.get("complete") is not True
        for p in pools
    ):
        errors.append("incomplete_natural_pool_selected")
    report: dict[str, Any] = {
        "unit": unit,
        "errors": sorted(set(errors)),
        "primary_metric": metric(unit, 0, len(ids), errors),
        "hypothesis_status": "invalidated" if errors else "mixed",
        "planned_tasks": len(ids),
        "observed_pools": len(records),
        "replacement_calls": replaced,
        "bootstrap_manifest_sha256": manifest_sha,
    }
    if errors:
        return report  # No grades are needed to diagnose an incomplete unit.
    outcomes = ss.score_selection(records, pools, graded=graded, aliases=aliases)
    name = METRICS[unit][0]
    summary = ss.summarize_outcomes(outcomes, deltas=[(name, SELECTORS[0], SELECTORS[1])])
    primary = summary["paired_deltas"][name]
    ci = interval(outcomes, manifest_sha, name)
    report.update(
        primary_metric=metric(unit, primary["numerator"], len(ids), []),
        summary=summary,
        confidence_interval=ci,
        outcomes=outcomes,
        discordant_counts={"b": primary["comparison_better"], "c": primary["baseline_better"]},
        split_summary={
            split: ss.summarize_outcomes([r for r in outcomes if r["split"] == split])
            for split in sorted({r["split"] for r in outcomes if r["split"] is not None})
        },
        judge_error_orders=sum(
            bool(row.get("judge_error"))
            for record in records
            for entry in record["selectors"].values()
            for row in entry["orders"].values()
        ),
    )
    if unit in ("U4", "X2"):
        if ci["lower"] is not None and ci["lower"] > -0.10:
            report["hypothesis_status"] = "supported"
        elif ci["upper"] is not None and ci["upper"] < -0.10:
            report["hypothesis_status"] = "not-supported"
    if unit == "X2":
        report["split_intervals"] = {
            split: interval(
                [r for r in outcomes if r["split"] == split], manifest_sha, f"{name}:{split}"
            )
            for split in report["split_summary"]
        }
    return report


def summarize_generation(
    spec: dict[str, Any],
    tasks: list[dict[str, Any]],
    payloads: dict[str, Any],
    saved_pools: list[Any],
    errors: list[str],
) -> dict[str, Any]:
    from evals.benchmarks import score_selection as ss

    errors = list(errors)
    ids = spec["reproduction"]["execution"]["ordered_workload_ids"]
    if len(ids) != 12 or [t["pool_id"] for t in tasks] != ids:
        raise ValueError("U5p needs the fixed 12 tasks")
    saved = {p.pool_id: p for p in saved_pools}
    if len(saved) != len(saved_pools) or not set(saved) <= set(ids) or set(payloads) != set(ids):
        errors.append("generation_payload_coverage")
    complete, excluded = [], []
    for task in tasks:
        pid = task["pool_id"]
        payload = payloads.get(pid)
        if payload is None:
            continue
        candidates = payload.get("tasks", [])
        if len(candidates) != 4 or any(r.get("success") is not True for r in candidates):
            errors.append(f"{pid}:incomplete_candidate_execution")
            continue
        # The registered size exclusion is a measured generation outcome, not
        # infrastructure invalidity. Every other native reconstruction error fails closed.
        too_long = any(len(ss.candidate_text(r.get("output"))) > 2000 for r in candidates)
        try:
            expected = ss.freeze_natural_pool(
                pool_id=pid,
                task=task["task"],
                case=task["case"],
                orders=task["orders"],
                payload=payload,
                cluster_id=task["cluster_id"],
            )
        except ValueError as error:
            if too_long and "at most 2000 characters" in str(error) and pid not in saved:
                excluded.append(pid)
                continue
            errors.append(f"{pid}:native_pool_reconstruction_failed")
            continue
        if pid not in saved or ss.pool_record(expected) != ss.pool_record(saved[pid]):
            errors.append(f"{pid}:saved_pool_differs_from_payload")
        elif len(expected.candidates) == 4 and expected.provenance.get("complete") is True:
            complete.append(pid)
    errors = sorted(set(errors))
    return {
        "unit": "U5p",
        "errors": errors,
        "hypothesis_status": "invalidated" if errors else "mixed",
        "primary_metric": metric("U5p", len(complete), 12, errors),
        "planned_tasks": 12,
        "complete_pool_ids": complete,
        "excluded_overlength_ids": excluded,
        "n_pool_valid": len(complete),
        "regeneration": False,
        "generation_usage_note": "Native sub-agent usage sums omit unknown inner-call coverage; "
        "missing usage is not zero and these sums are not full billing totals.",
    }


def record_bundle(
    directory: Path, spec: dict[str, Any], report: dict[str, Any], evidence: list[Path]
) -> None:
    import track_common as tc
    from scripts.eval.contract import validate_run_bundle

    for name in ("results.json", "attempts.jsonl", "analysis.json"):
        if (directory / name).exists():
            raise FileExistsError(f"preserve existing {name}; use a new lineage")
    report = {
        **report,
        "run_id": spec["run_id"],
        "source_revision": spec["reproduction"]["geode"]["revision"],
        "run_spec_sha256": sha(directory / "run-spec.json"),
        "analysis_entry_sha256": sha(Path(__file__)),
        "source_sha256": {str(p.relative_to(directory)): sha(p) for p in evidence},
    }
    report["interval_metrics"] = {
        bound: {
            "value": value if value is not None else "not-measurable",
            "numerator": value,
            "denominator": 1 if value is not None else None,
        }
        for bound in ("lower", "upper")
        for value in [(report.get("confidence_interval") or {}).get(bound)]
    }
    tc.write_new(directory / "results.json", report)
    refs = [
        {"kind": "native-result", "path": "results.json", "sha256": sha(directory / "results.json")}
    ]
    refs += [
        {"kind": "other", "path": str(p.relative_to(directory)), "sha256": sha(p)} for p in evidence
    ]
    stamp, invalid = tc.now(), bool(report["errors"])
    attempt_id = f"{spec['run_id']}-score-analysis"
    attempt = {
        "schema_id": "geode.eval-attempt@1",
        "schema_version": 1,
        "run_id": spec["run_id"],
        "attempt_id": attempt_id,
        "parent_attempt_id": None,
        "sequence": 0,
        "timing": {
            "status": "exact",
            "started_at": stamp,
            "finished_at": stamp,
            "source_ref": None,
        },
        "validity": "invalid" if invalid else "valid",
        "outcome": "unknown" if invalid else "mixed",
        "change": {
            "surface": "analysis-only",
            "description": "Derived native Score aggregate; "
            "timestamp measures analysis, not model dispatch. Raw evidence is preserved.",
        },
        "expected_effect": "Apply the frozen Score metric and source-cluster interval "
        "without new inference.",
        "observed_result": f"{report['primary_metric']}; errors={report['errors']}",
        "failure_class": report["errors"][0] if invalid else None,
        "error_ref": None,
        "evidence_refs": refs,
        "selected_for_analysis": True,
    }
    tc.write_new(directory / "attempts.jsonl", json.dumps(attempt, ensure_ascii=False) + "\n")
    analysis = {
        "schema_id": "geode.eval-analysis@1",
        "schema_version": 1,
        "run_id": spec["run_id"],
        "analyzed_at": tc.now(),
        "run_spec_sha256": sha(directory / "run-spec.json"),
        "attempts_sha256": sha(directory / "attempts.jsonl"),
        "selected_attempt_ids": [attempt_id],
        "answer": f"{report['unit']}: {report['primary_metric']['value']}; "
        f"frozen diagnostic decision {report['hypothesis_status']}.",
        "metrics": [
            {
                **report["primary_metric"],
                "unit": spec["study"]["primary_metric"]["unit"],
                "source_ref": "results.json",
                "source_locator": {
                    k: f"/primary_metric/{k}" for k in ("value", "numerator", "denominator")
                },
            }
        ],
        "decision": {
            "outcome": "diagnostic-only",
            "hypothesis_status": report["hypothesis_status"],
            "rationale": "05 §3.4; U4/X2 strict -0.10 CI bounds; U5 descriptive mixed. "
            "Selected infrastructure invalidity is not measurable.",
        },
        "limitations": [
            "No superiority or latency claim; no external tuning or p-value.",
            "Missing usage stays unknown; analysis timestamps are not execution timing.",
            "Candidate width and two presentation orders are not independent repetitions.",
            "Intervals below 10 source clusters are unavailable; split strata are descriptive.",
            "Signed CI bounds stay in digest-bound results.json /interval_metrics: native v1 "
            "forbids negative secondary numerators, so no lossy secondary projection is made.",
        ],
        "evidence_refs": refs,
    }
    tc.write_new(directory / "analysis.json", analysis)
    validate_run_bundle(directory / "run-spec.json")


def main(argv: list[str] | None = None) -> int:
    import gen_driver
    import score_driver
    from evals.benchmarks import score_selection as ss
    from scripts.eval.contract import validate_run_spec

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unit", choices=METRICS, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--input-manifest", type=Path, action="append", default=[])
    parser.add_argument("--graded", type=Path, action="append", default=[])
    parser.add_argument("--aliases", type=Path, action="append", default=[])
    parser.add_argument("--strata", type=Path, help="X2 gold metadata, only after reviewed unseal")
    parser.add_argument(
        "--generation", type=Path, help="U5p completed phase for U5s denominator binding"
    )
    parser.add_argument("--unsealed-reviewed", action="store_true")
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args(argv)
    driver = gen_driver if args.unit == "U5p" else score_driver
    directory = driver.phase_dir(args.unit)
    spec = validate_run_spec(directory / "run-spec.json")
    manifest_sha = check_spec(args.unit, spec, args.manifest)
    frozen, inputs = driver.preflight(args.unit)
    if frozen["run_id"] != spec["run_id"]:
        raise ValueError("frozen run identity differs")
    errors, evidence = execution_evidence(
        directory,
        "U5p-gen" if args.unit == "U5p" else args.unit,
        frozen,
        allowed_exit=(0, 1) if args.unit == "U5p" else (0,),
    )
    external = {str(args.manifest.resolve()): manifest_sha}
    declared = declared_digests(read(args.manifest)) | declared_digests(spec)
    for path in args.input_manifest:
        if sha(path) not in declared:
            raise ValueError("input manifest digest was not registered before dispatch")
        declared |= declared_digests(read(path))
        external[str(path.resolve())] = sha(path)
    tolerance = None
    if args.unit != "U5p":
        tolerance_path = Path(read(directory / "score-tolerance.json")["source"])
        if frozen["sha256"].get(str(tolerance_path.resolve())) != sha(tolerance_path):
            raise ValueError("main freeze did not bind the U0b tolerance authority")
        tolerance = tolerance_authority(tolerance_path)
        if {k: tolerance[k] for k in ("sum_tolerance", "score_tolerance")} != frozen["tolerances"]:
            raise ValueError("main selector bounds differ from U0b")
        external[str(tolerance_path.resolve())] = sha(tolerance_path)
    if args.unit == "U5p":
        payloads = {}
        for task in inputs:
            path = directory / "payloads" / f"{task['pool_id']}.json"
            if path.exists():
                evidence.append(path)
                payloads[task["pool_id"]] = read(path)
        pool_path = directory / "pools.natural.jsonl"
        pools = ss.load_pools(pool_path) if pool_path.exists() else []
        for name in ("pools.natural.jsonl", "generation-usage.jsonl", "pool-errors.jsonl"):
            if (directory / name).exists():
                evidence.append(directory / name)
        report = summarize_generation(spec, inputs, payloads, pools, errors)
        block = directory / "private-receipts" / f"{frozen['run_id']}-block.json"
        exit_path = directory / "execution-receipt.json"
        if block.exists() and read(block).get("frozen_pools") != len(pools):
            errors.append("saved_generation_pool_count_mismatch")
        if exit_path.exists() and read(exit_path).get("exit_code") != (
            0 if len(pools) == 12 else 1
        ):
            errors.append("generation_exit_does_not_match_native_completion")
        if errors != report["errors"]:
            report = summarize_generation(spec, inputs, payloads, pools, errors)
        if not report["errors"]:
            from evals.benchmarks.decision_metrics import bootstrap_seed, cluster_bootstrap

            completed = set(report["complete_pool_ids"])
            clusters = {t["cluster_id"]: [int(t["pool_id"] in completed)] for t in inputs}
            report["confidence_interval"] = cluster_bootstrap(
                clusters,
                lambda sample: sum(sample) / len(sample),
                seed=bootstrap_seed(manifest_sha, METRICS["U5p"][0]),
            ).as_dict()
    else:
        path = directory / "dispatch-records.jsonl"
        records = rows(path) if path.exists() else []
        if path.exists():
            evidence.append(path)
        if (directory / "timings.json").exists():
            evidence.append(directory / "timings.json")
        graded, aliases = None, None
        if not errors and args.unit in ("U4", "X2"):
            if not args.unsealed_reviewed or not args.graded:
                parser.error("complete U4/X2 analysis needs reviewed grade release and --graded")
            graded, aliases = {}, {}
            for file, loader, target in (
                *[(p, ss.load_graded_pools, graded) for p in args.graded],
                *[(p, ss.load_aliases, aliases) for p in args.aliases],
            ):
                if sha(file) not in declared:
                    raise ValueError("grade/alias digest is absent from preregistered manifests")
                values = loader(file)
                if set(values) & set(target):
                    raise ValueError("duplicate grade or alias identities across inputs")
                target.update(values)
                external[str(file.resolve())] = sha(file)
            if not args.aliases:
                aliases = None
            else:
                # A mixed selection/test input uses identity IDs in selection
                # and sealed aliases in test. Complete the native join map only
                # for identities independently present in the graded pool.
                for pool in inputs:
                    if pool.pool_id in graded:
                        aliases.setdefault(pool.pool_id, pool.pool_id)
                        for candidate in pool.candidates:
                            if candidate.candidate_id in graded[pool.pool_id].grades:
                                aliases.setdefault(candidate.candidate_id, candidate.candidate_id)
        if args.unit == "U5s":
            if args.generation is None:
                parser.error("U5s needs --generation for the fixed valid-pool denominator")
            from scripts.eval.contract import validate_run_bundle

            validate_run_bundle(args.generation / "run-spec.json")
            generation = read(args.generation / "results.json")
            if generation["errors"] or generation["complete_pool_ids"] != frozen["workload_ids"]:
                raise ValueError("U5s workloads differ from measured U5p valid pools")
            natural = args.generation / "pools.natural.jsonl"
            if frozen["sha256"].get(str(natural.resolve())) != sha(natural):
                raise ValueError("U5s freeze did not bind the completed U5p pool bytes")
            external[str(args.generation / "results.json")] = sha(args.generation / "results.json")
        report = summarize_score(
            args.unit,
            spec,
            frozen,
            inputs,
            records,
            errors,
            manifest_sha,
            graded=graded,
            aliases=aliases,
        )
        if args.unit == "X2" and not report["errors"]:
            if args.strata is None:
                parser.error(
                    "X2 needs reviewed --strata metadata for registered descriptive slices"
                )
            if sha(args.strata) not in declared:
                raise ValueError("X2 metadata digest differs from the frozen external manifest")
            metadata_rows = rows(args.strata)
            metadata = {r["pool_id"]: r for r in metadata_rows}
            if len(metadata) != len(metadata_rows) or set(metadata) != set(frozen["workload_ids"]):
                raise ValueError("X2 metadata does not cover the exact frozen workloads")
            for row in report["outcomes"]:
                if row["best_ids"] != [metadata[row["pool_id"]]["positive_candidate_id"]]:
                    raise ValueError("X2 metadata target disagrees with graded pool")
            report["strata"] = {}
            for field in ("op", "step_index", "positive_tag", "positive_has_text_or_attributes"):
                groups: dict[str, list[Any]] = defaultdict(list)
                for row in report["outcomes"]:
                    groups[str(metadata[row["pool_id"]][field])].append(row)
                report["strata"][field] = {k: ss.summarize_outcomes(v) for k, v in groups.items()}
            external[str(args.strata.resolve())] = sha(args.strata)
    report["external_evidence_sha256"] = external
    if tolerance is not None:
        report["u5_descriptive_only"] = tolerance["u5_descriptive_only"]
        report["frozen_tolerances"] = frozen["tolerances"]
    if args.record:
        record_bundle(directory, spec, report, evidence)
    print(
        json.dumps(
            {k: report[k] for k in ("unit", "primary_metric", "hypothesis_status", "errors")},
            indent=2,
        )
    )
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
