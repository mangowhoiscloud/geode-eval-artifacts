"""Bind existing #2 U2s/U3 native aggregates to analysis.json, without reading gold.

Run the pinned native aggregate producer once after the authorized unseal. This
entry then records only analysis.json; it never dispatches or rewrites attempts.
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
CONFIG = {
    "U2s": ("stability-results.json", ("choice", "noul"), 384),
    "U3": ("latency-results.json", ("choice",), 240),
}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> Any:
    require(
        not any("DO-NOT-OPEN" in p or "sealed" in p or p == "private-secrets" for p in path.parts),
        "protected input path",
    )
    return json.loads(path.read_text())


def prepare(
    source: Path,
    phase: Path,
    unit: str,
    manifest: Path,
    selection: Path,
    normalization: Path | None,
) -> tuple[Any, Any, Any, Any]:
    filename, primitives, count = CONFIG[unit]
    frozen = load(phase / "freeze.json")
    require(frozen["unit"] == unit and frozen["source_revision"] == REVISION, "wrong freeze")
    for name in ("panel_driver.py", "track_common.py", "source_pin.py", "run_guards.py"):
        path = phase.parent / name
        require(frozen["sha256"].get(str(path)) == sha(path), f"driver changed: {name}")
    sys.path[:0] = [str(source), str(phase.parent)]
    driver = importlib.import_module("panel_driver")
    require(Path(driver.__file__).resolve().parent == phase.parent, "different driver imported")
    pinned, revision = driver.tc.pinned_source()
    require(pinned == source and revision == REVISION, "source pin differs")
    require(driver.phase_dir(unit).resolve() == phase, "phase differs")
    frozen, _ = driver.preflight(unit)
    require(len(frozen["cells"]) == count, "planned matrix count differs")
    panel = importlib.import_module("evals.benchmarks.verdict_panel_runner")
    contract = importlib.import_module("scripts.eval.contract")
    require(Path(panel.__file__).resolve().is_relative_to(source), "different source imported")
    public = load(manifest)
    require(
        public["splits"]["test"]["states_sha256"] == sha(Path(frozen["states"])),
        "public state binding differs",
    )
    require(
        load(selection)["schema_id"] == "geode.jev-selection-freeze@1", "wrong selection freeze"
    )
    specs = {}
    for primitive in primitives:
        spec = contract.validate_run_spec(phase / f"run-spec.{primitive}.json")
        require(spec["run_id"] == frozen["run_ids"][primitive], "run identity differs")
        require(spec["reproduction"]["geode"]["revision"] == REVISION, "spec source differs")
        require(spec["preregistration"]["status"] == "frozen", "spec not frozen")
        require(
            spec["reproduction"]["execution"]["ordered_workload_ids"] == frozen["workload_ids"],
            "workload order differs",
        )
        plan = spec["study"]["analysis_plan"]
        require(f"selection-freeze sha256: {sha(selection)}" in plan, "selection freeze differs")
        require(
            f"post-U1 analysis entry sha256:{sha(Path(__file__))}" in plan,
            "analysis entry not registered",
        )
        require(
            f"test public manifest sha256:{sha(manifest)}"
            in spec["reproduction"]["environment"]["initial_state_ref"],
            "public manifest differs",
        )
        for key, value in {
            "native_results": f"{primitive}/{filename}",
            "attempts": f"{primitive}/attempts.jsonl",
            "analysis": f"{primitive}/analysis.json",
        }.items():
            require(spec["artifacts"][key] == value, f"artifact path differs: {key}")
        specs[primitive] = spec
    if unit == "U2s":
        require(normalization is not None, "normalization manifest required")
        normalized = load(normalization)
        require(
            normalized["output_sha256"] == sha(Path(frozen["paraphrases"])),
            "paraphrase output differs",
        )
        for spec in specs.values():
            plan = spec["study"]["analysis_plan"]
            require(
                f"U2s paraphrase normalization sha256:{sha(normalization)}" in plan
                and f"U2s normalized questions sha256:{normalized['output_sha256']}" in plan,
                "normalization binding not registered",
            )
    return panel, contract, frozen, specs


def closure(phase: Path, frozen: Any, unit: str, receipt: Path) -> None:
    done = load(receipt)
    require(
        type(done.get("exit_code")) is int and done["exit_code"] == 0,
        "completed guarded driver exit 0 required",
    )
    require(
        done.get("unit") == unit
        and done.get("source_revision") == REVISION
        and done.get("freeze_sha256") == sha(phase / "freeze.json")
        and done.get("driver_sha256") == frozen["driver_sha256"],
        "execution receipt differs",
    )
    count = CONFIG[unit][2]
    dispatch = load(phase / "dispatch-summary.json")
    require(
        dispatch.get("stopped") is False
        and dispatch.get("stop_reason") is None
        and dispatch.get("planned_calls") == dispatch.get("dispatched_calls") == count,
        "incomplete/invalid dispatch; preserve native failure and use failure analysis",
    )
    block = load(phase / "private-receipts" / f"{frozen['run_ids']['choice']}-block.json")
    require(
        block.get("unit") == unit
        and block.get("run_id") == frozen["run_ids"]["choice"]
        and block.get("source_revision") == REVISION
        and block.get("freeze_sha256") == sha(phase / "freeze.json")
        and block.get("account_matches_g0") is True
        and block.get("lock_mode") == ("latency-solo" if unit == "U3" else "panel-unit")
        and block.get("planned_calls") == block.get("dispatched_calls") == count
        and block.get("stop_reason") is None,
        "block guards differ",
    )


def analyses(
    phase: Path, unit: str, frozen: Any, specs: Any, manifest: Path, panel: Any, contract: Any
) -> dict[str, Any]:
    filename, primitives, _ = CONFIG[unit]
    outputs = {p: phase / p for p in primitives}
    # Gold-free recomputation checks the primary only; gold-based auxiliaries stay
    # in the existing digest-bound report produced after authorized unseal.
    recomputed = (
        panel.stability_report(outputs, frozen["workload_ids"])
        if unit == "U2s"
        else panel.latency_report(
            outputs["choice"], frozen["workload_ids"], split_manifest_sha256=sha(manifest)
        )
    )
    result = {}
    for primitive in primitives:
        run = outputs[primitive]
        report = load(run / filename)
        require(report["gold_attached"] is True, "record aggregate once after authorized unseal")
        current = report["runs"][primitive]["primary"] if unit == "U2s" else report["primary"]
        expected = (
            recomputed["runs"][primitive]["primary"] if unit == "U2s" else recomputed["primary"]
        )
        require(current == expected, "native primary differs from retained attempts")
        rows = contract.validate_attempts(run / "attempts.jsonl")
        require(
            all(r["run_id"] == specs[primitive]["run_id"] for r in rows), "mixed run identities"
        )
        selected = [r for r in rows if r["selected_for_analysis"]]
        aggregates = [r for r in selected if r["change"]["surface"] == "analysis-only"]
        require(
            len(aggregates) == 1
            and aggregates[0]["evidence_refs"]
            == [{"kind": "native-result", "path": filename, "sha256": sha(run / filename)}],
            "expected one bound native aggregate",
        )
        require(not (run / "analysis.json").exists(), "analysis exists; do not overwrite")
        refs = {
            json.dumps(ref, sort_keys=True): ref for r in selected for ref in r["evidence_refs"]
        }
        metric_rows = (
            panel.stability_metric_rows(report, primitive=primitive)
            if unit == "U2s"
            else panel.latency_metric_rows(report)
        )
        invalid = current["value"] == "not-measurable"
        status = "invalidated" if invalid else "mixed" if unit == "U2s" else current["decision"]
        result[primitive] = {
            "schema_id": "geode.eval-analysis@1",
            "schema_version": 1,
            "run_id": specs[primitive]["run_id"],
            "analyzed_at": datetime.now(UTC).isoformat(),
            "run_spec_sha256": sha(phase / f"run-spec.{primitive}.json"),
            "attempts_sha256": sha(run / "attempts.jsonl"),
            "selected_attempt_ids": [r["attempt_id"] for r in selected],
            "answer": "Descriptive repeated-question stability; variants are not replications."
            if unit == "U2s"
            else "Paired within-state dispatch-to-completion latency.",
            "metrics": metric_rows,
            "decision": {
                "outcome": "diagnostic-only",
                "hypothesis_status": status,
                "rationale": specs[primitive]["study"]["decision_rule"],
            },
            "limitations": [
                "Shared account external usage remains unknown.",
                "No model call, gold read or metric refit by this analysis connector.",
                "Native aggregate is retained; a replay is not score authority.",
            ],
            "evidence_refs": list(refs.values()),
        }
    return result


def record(phase: Path, documents: dict[str, Any], panel: Any, contract: Any) -> None:
    require(not any((phase / p / "analysis.json").exists() for p in documents), "analysis exists")
    for primitive, document in documents.items():
        panel._write_new(
            phase / primitive / "analysis.json",
            json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        )
        contract.validate_run_bundle(phase / f"run-spec.{primitive}.json")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "phase", "manifest", "selection-freeze"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--unit", choices=CONFIG, required=True)
    parser.add_argument("--normalization", type=Path)
    parser.add_argument("--execution-receipt", type=Path)
    parser.add_argument("--check-inputs", action="store_true")
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args()
    require(not (args.check_inputs and args.record), "choose check-inputs or record")
    panel, contract, frozen, specs = prepare(
        args.source.resolve(),
        args.phase.resolve(),
        args.unit,
        args.manifest.resolve(),
        args.selection_freeze.resolve(),
        args.normalization,
    )
    if args.check_inputs:
        print(json.dumps({"ready": True, "unit": args.unit, "model_calls": 0}))
        return 0
    require(args.execution_receipt is not None, "execution receipt required")
    closure(args.phase, frozen, args.unit, args.execution_receipt)
    documents = analyses(args.phase, args.unit, frozen, specs, args.manifest, panel, contract)
    if args.record:
        record(args.phase, documents, panel, contract)
    print(json.dumps({p: d["decision"] for p, d in documents.items()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
