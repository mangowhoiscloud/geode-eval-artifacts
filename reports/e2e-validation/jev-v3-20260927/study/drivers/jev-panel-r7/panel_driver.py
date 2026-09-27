"""Private P-track driver for verdict and intent panels (including U6a, U0c-i).

  --freeze --unit U --run-spec F [--run-spec G] --states S [--paraphrases P] --reviewed
  --preflight --unit U
  --execute --unit U --reviewed [--quota-live]

The library ``PanelRunner`` (PR head) owns dispatch order, pacing, heartbeat, the
§4.2 substitution rule and error classes; this driver only builds its arguments
from the frozen run-spec(s), constructs GEODE's standard engine routes (Astra: the
subscription adapter; Jev: the TypeSafe client with the key from GEODE settings)
and wraps the unit in the host guards. A two-primitive unit (U0a, U1, U2, U2s) is
one PanelUnit over the sibling Choice and Noul run-specs. U3 is the solo
paired-latency unit. U6a/U0c-i take an I-panel JSON via --states and use the
inbox helper in paired-latency mode under the normal panel lock. No mode here
calls a model except ``--execute --reviewed``.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import track_common as tc  # noqa: E402

LOCAL_FILES = (
    "panel_driver.py",
    "track_common.py",
    "run_guards.py",
    "source_pin.py",
    "source-pin.json",
)
PREFIX = "geode-jev-verdict-panel-"
UNITS: dict[str, dict[str, Any]] = {
    "U0a": {"specs": {"choice": PREFIX + "admission-choice-", "noul": PREFIX + "admission-noul-"}},
    "U1": {"specs": {"choice": PREFIX + "selection-choice-", "noul": PREFIX + "selection-noul-"}},
    "U2": {"specs": {"choice": PREFIX + "test-choice-", "noul": PREFIX + "test-noul-"}},
    "U2s": {
        "specs": {"choice": PREFIX + "stability-choice-", "noul": PREFIX + "stability-noul-"},
        "paraphrases": True,
    },
    "U3": {
        "specs": {"choice": PREFIX + "latency-"},
        "mode": "paired-latency",
        "concurrency": 2,
        "lock": "latency-solo",
    },
    "X1a": {"specs": {"choice": "geode-jev-external-cuavb-choice-admission-"}},
    "X1": {"specs": {"choice": "geode-jev-external-cuavb-choice-"}},
    "U6a": {
        "specs": {"choice": "geode-jev-choice-intent-panel-"},
        "judgment": "intent",
        "mode": "paired-latency",
        "concurrency": 2,
    },
    "U0c-i": {
        "specs": {"choice": "geode-jev-choice-intent-panel-admission-"},
        "judgment": "intent",
        "mode": "paired-latency",
        "concurrency": 2,
    },
}
PACING_S, HEARTBEAT_S = 1.0, 5.0
TIMEOUTS = {"llm": 180.0, "jev": 60.0}


def config(unit: str) -> dict[str, Any]:
    base = {
        "mode": "latin",
        "concurrency": 4,
        "lock": "panel-unit",
        "paraphrases": False,
        "judgment": "verdict",
    }
    return {**base, **UNITS[unit]}


def phase_dir(unit: str) -> Path:
    return HERE / unit.lower()


def driver_sha() -> str:
    return tc.sha(HERE / "panel_driver.py")


def read_states(path: Path, *, judgment: str = "verdict") -> list[dict[str, Any]]:
    if judgment == "intent":
        from evals.benchmarks.verdict_panel_runner import intent_panel_rows

        return intent_panel_rows(tc.read(path))
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def build_cells(
    unit: str, workloads: list[Any], run_ids: dict[str, str], source: Path, revision: str
) -> list[dict[str, Any]]:
    """Frozen cells in dispatch order: the library's Latin rotation over the unit's cells."""
    from evals.benchmarks.decision_verification import contract_digests
    from evals.benchmarks.verdict_panel_runner import CELLS, latin_cells

    cfg = config(unit)
    cells = tuple(cell for cell in CELLS if cell[1] in run_ids)
    verifier_name = (
        "decision_handoff.py" if cfg["judgment"] == "intent" else "decision_verification.py"
    )
    verifier = tc.sha(source / "evals/benchmarks" / verifier_name)
    rows = []
    for index, workload in enumerate(workloads):
        state_sha = hashlib.sha256(tc.canonical(workload.state).encode()).hexdigest()
        for position, (engine, primitive) in enumerate(latin_cells(index, cells)):
            policy = {
                "route": tc.ASTRA_ROUTE if engine == "llm" else tc.JEV_ROUTE,
                "primitive": primitive,
                "variant": workload.variant,
                "mode": cfg["mode"],
                "max_concurrency": cfg["concurrency"],
                "pacing_s": PACING_S,
                "timeout_s": TIMEOUTS[engine],
                "llm_max_retries": 1,
                "substitution": "05 §4.2: one replacement, stop above 2%",
                "source_revision": revision,
            }
            contract = contract_digests(primitive)
            if cfg["judgment"] == "intent":
                from evals.benchmarks.decision_handoff import INBOX_HELPER_CONTRACT

                policy.update(judgment="intent", choice_probability_sum_tolerance=1e-5)
                contract = {
                    "contract": INBOX_HELPER_CONTRACT,
                    "source_sha256": verifier,
                }
            rows.append(
                {
                    "index": len(rows),
                    "state_index": index,
                    "position": position,
                    "workload_id": workload.workload_id,
                    "state_id": workload.state_id,
                    "cluster_id": workload.cluster_id,
                    "variant": workload.variant,
                    "engine": engine,
                    "primitive": primitive,
                    "run_id": run_ids[primitive],
                    **tc.cell_digests(
                        policy,
                        case_sha256=state_sha,
                        task_checksum=hashlib.sha256(tc.canonical(contract).encode()).hexdigest(),
                        verifier_sha256=verifier,
                    ),
                }
            )
    return rows


def freeze(unit: str, specs: list[Path], states: Path, paraphrases: Path | None) -> dict[str, Any]:
    from evals.benchmarks.verdict_panel_runner import workloads_from_states
    from scripts.eval.contract import validate_run_spec

    source, revision = tc.pinned_source()
    if source_pin_revision(source) != revision:
        raise ValueError("pinned checkout moved")
    cfg = config(unit)
    if len(specs) != len(cfg["specs"]):
        raise ValueError(f"{unit} needs run-specs for {sorted(cfg['specs'])}")
    loaded = {
        primitive: (path, validate_run_spec(path))
        for primitive, path in zip(cfg["specs"], specs, strict=True)
    }
    ids = None
    for primitive, (_, spec) in loaded.items():
        these = tc.check_spec(
            spec,
            prefix=cfg["specs"][primitive],
            revision=revision,
            driver_sha256=driver_sha(),
            max_concurrency=cfg["concurrency"],
        )
        if ids is not None and these != ids:
            raise ValueError("sibling run-specs must list the same workloads in the same order")
        ids = these
    assert ids is not None
    if cfg["paraphrases"] != (paraphrases is not None):
        raise ValueError("U2s needs its frozen paraphrases; other units take none")
    workloads = workloads_from_states(read_states(states, judgment=cfg["judgment"]), ids)
    if cfg["judgment"] == "intent" and any(workload.variant != "base" for workload in workloads):
        raise ValueError("I-panel families have no question variants")
    run_ids = {primitive: spec["run_id"] for primitive, (_, spec) in loaded.items()}
    directory = phase_dir(unit)
    directory.mkdir(mode=0o700)
    copies = []
    for primitive, (path, _) in loaded.items():
        copy = directory / f"run-spec.{primitive}.json"
        tc.write_new(copy, path.read_text(encoding="utf-8"))
        copies.append(copy)
    cells = build_cells(unit, workloads, run_ids, source, revision)
    planned_astra = sum(
        spec["reproduction"]["execution"]["budget"]["limit"] for _, spec in loaded.values()
    )
    record = {
        "schema": "jev-v3.panel-freeze@1",
        "unit": unit,
        "run_ids": run_ids,
        "frozen_at": tc.now(),
        "source_revision": revision,
        "mode": cfg["mode"],
        "judgment": cfg["judgment"],
        "lock_mode": cfg["lock"],
        "max_concurrency": cfg["concurrency"],
        "pacing_s": PACING_S,
        "heartbeat_s": HEARTBEAT_S,
        "timeouts": TIMEOUTS,
        "workload_ids": ids,
        "states": str(states.resolve()),
        "paraphrases": str(paraphrases.resolve()) if paraphrases else None,
        "cells": cells,
        "planned_calls": len(cells),
        "planned_astra_call_cap": planned_astra,
        "planned_jev_calls": sum(cell["engine"] == "jev" for cell in cells),
        "driver_sha256": driver_sha(),
        "sha256": tc.bound_inputs(
            [
                *copies,
                states.resolve(),
                *([paraphrases.resolve()] if paraphrases else []),
                *(HERE / name for name in LOCAL_FILES),
                source / "evals/benchmarks/verdict_panel_runner.py",
                source / "evals/benchmarks/decision_verification.py",
                *(
                    [source / "evals/benchmarks/decision_handoff.py"]
                    if cfg["judgment"] == "intent"
                    else []
                ),
            ]
        ),
    }
    tc.write_new(directory / "freeze.json", record)
    print(f"{unit}: frozen {len(cells)} calls over {len(ids)} workloads; no model call")
    return record


def source_pin_revision(source: Path) -> str:
    import source_pin

    return source_pin.clean_revision(source)


def preflight(unit: str) -> tuple[dict[str, Any], list[Any]]:
    from evals.benchmarks.verdict_panel_runner import workloads_from_states

    source, revision = tc.pinned_source()
    frozen = tc.read(phase_dir(unit) / "freeze.json")
    if (
        frozen["unit"] != unit
        or frozen["source_revision"] != revision
        or source_pin_revision(source) != revision
    ):
        raise ValueError(f"{unit}: freeze belongs to another unit or source")
    tc.check_bound(frozen["sha256"])
    workloads = workloads_from_states(
        read_states(Path(frozen["states"]), judgment=config(unit)["judgment"]),
        frozen["workload_ids"],
    )
    rebuilt = build_cells(unit, workloads, frozen["run_ids"], source, revision)
    if rebuilt != frozen["cells"]:
        raise ValueError(f"{unit}: frozen cells changed")
    return frozen, workloads


# Diagnostic values only: unknown codes stay null, never become classification input.
_ERROR_IDENTIFIERS = frozenset(
    {
        "server_error",
        "internal_error",
        "internal_server_error",
        "overloaded",
        "overloaded_error",
        "server_overloaded",
        "rate_limit_exceeded",
        "rate_limit_error",
        "quota_exhausted",
        "insufficient_quota",
        "usage_limit_reached",
        "usage_not_included",
        "plan_limit_reached",
        "billing_error",
        "billing_hard_limit_reached",
        "billing_not_active",
        "invalid_request_error",
        "invalid_prompt",
        "authentication_error",
        "permission_error",
        "request_timeout",
        "timeout",
        "api_error",
    }
)
_REQUEST_ID = re.compile(r"(?:req_[0-9a-f]{32}|[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})")


def _safe_error_metadata(error: BaseException) -> dict[str, str | int | None]:
    """Keep four bounded identifiers; never inspect message, body, request or headers."""
    empty: dict[str, str | int | None] = dict.fromkeys(("code", "type", "status", "request_id"))
    try:
        code, kind = getattr(error, "code", None), getattr(error, "type", None)
        status, request_id = getattr(error, "status_code", None), getattr(error, "request_id", None)
        return {
            "code": code
            if type(code) is str and len(code) <= 64 and code in _ERROR_IDENTIFIERS
            else None,
            "type": kind
            if type(kind) is str and len(kind) <= 64 and kind in _ERROR_IDENTIFIERS
            else None,
            "status": status if type(status) is int and 100 <= status <= 599 else None,
            "request_id": request_id
            if type(request_id) is str
            and len(request_id) == 36
            and _REQUEST_ID.fullmatch(request_id)
            else None,
        }
    except Exception:
        # Diagnostic attribute access must not replace the original failure.
        return empty


def guarded_runner_class() -> type:
    """Native dispatch with a pre-call guard and bounded, call-local error metadata."""
    from evals.benchmarks.verdict_panel_runner import PanelRunner

    class GuardedPanelRunner(PanelRunner):
        control: tc.CallControl

        async def _call_once(self, workload, engine, primitive, position=None):  # type: ignore[no-untyped-def]
            status, evidence, error = await super()._call_once(
                workload, engine, primitive, position
            )
            if error is not None:
                evidence = {**evidence, "error_metadata": _safe_error_metadata(error)}
            return status, evidence, error

        async def _dispatch(self, workload, engine, primitive, position=None):  # type: ignore[no-untyped-def]
            reason = self.control.before_call(engine)
            if reason is not None:
                self._stop(reason)
                return []
            return await super()._dispatch(workload, engine, primitive, position)

    return GuardedPanelRunner


async def execute(
    unit: str, *, quota_live: bool, engines: Any = None, solo_check: Any = None
) -> int:
    """Run one frozen unit under the host guards; ``engines`` is injected only by mock tests."""
    import httpx
    from evals.benchmarks.jev_cost_ledger import PanelSpendGuard
    from evals.benchmarks.verdict_panel_runner import PanelUnit

    frozen, workloads = preflight(unit)
    cfg = config(unit)
    directory = phase_dir(unit)
    first_run_id = frozen["run_ids"]["choice"]
    margin = int(
        frozen["planned_calls"] / cfg["concurrency"] * max(TIMEOUTS.values())
        + tc.AUTH_MARGIN_SLACK_S
    )
    admission = tc.admit(
        directory,
        unit=unit,
        run_id=first_run_id,
        lock_mode=cfg["lock"],
        planned_astra=frozen["planned_astra_call_cap"],
        planned_jev=frozen["planned_jev_calls"],
        required_margin_s=margin,
        quota_live=quota_live,
        solo_check=(solo_check or tc.docker_busy) if cfg["lock"] == "latency-solo" else None,
    )
    if admission is None:
        return 3
    summary: dict[str, Any] = {}
    secrets: list[str] = []
    try:
        tc.pin_runtime_settings()
        if engines is None:
            llm, key = tc.astra_adapter(), tc.load_typesafe_key()
            client = httpx.AsyncClient(timeout=TIMEOUTS["jev"] + 10)
        else:
            llm, client, key = engines
        secrets.append(key.get_secret_value())
        paraphrases = tc.read(Path(frozen["paraphrases"])) if frozen["paraphrases"] else {}
        panel_unit = PanelUnit(
            run_ids=frozen["run_ids"],
            outputs={primitive: directory / primitive for primitive in frozen["run_ids"]},
            session_dir=directory / "session",
            pacing_s=frozen["pacing_s"],
            max_concurrency=frozen["max_concurrency"],
            heartbeat_s=frozen["heartbeat_s"],
            paraphrases=paraphrases,
            timeouts=frozen["timeouts"],
            mode=frozen["mode"],
            judgment=cfg["judgment"],
        )
        runner = guarded_runner_class()(
            panel_unit,
            workloads,
            llm_adapter=llm,
            jev_client=client,
            jev_key=key,
            jev_guard=PanelSpendGuard(admission.ledger, first_run_id),
        )
        runner.control = tc.CallControl(admission, reader=tc.live_snapshot if quota_live else None)
        try:
            summary = await runner.run()
        finally:
            if engines is None:
                await client.aclose()
        tc.write_new(
            directory / "dispatch-summary.json", {**summary, "unit": unit, "lock_mode": cfg["lock"]}
        )
        tc.block_receipt(
            admission,
            block_id=unit,
            lock_mode=cfg["lock"],
            source_revision=frozen["source_revision"],
            freeze_sha256=tc.sha(directory / "freeze.json"),
            extra={
                "planned_calls": frozen["planned_calls"],
                "dispatched_calls": summary.get("dispatched_calls"),
                "stop_reason": summary.get("stop_reason"),
                "max_dispatch_skew_s": summary.get("max_dispatch_skew_s"),
                "in_flight_panel_calls": max_in_flight(directory / "session"),
            },
        )
    finally:
        astra = astra_usage(directory, frozen["run_ids"])
        admission.close(astra_calls=astra[0], astra_input_tokens=astra[1])
        tc.assert_no_secret(directory, secrets)
    print(
        json.dumps(
            {
                "unit": unit,
                "stopped": summary.get("stopped"),
                "stop_reason": summary.get("stop_reason"),
            }
        )
    )
    return 0 if summary and not summary.get("stopped") else 1


def max_in_flight(session: Path) -> int | None:
    path = session / "pair-log.jsonl"
    if not path.is_file():
        return None
    values = [
        attempt.get("in_flight_panel_calls")
        for line in path.read_text(encoding="utf-8").splitlines()
        for attempts in json.loads(line)["calls"].values()
        for attempt in attempts
    ]
    known = [value for value in values if isinstance(value, int)]
    return max(known) if known else None


def astra_usage(directory: Path, run_ids: dict[str, str]) -> tuple[int, int]:
    """Astra calls and input tokens from the retained receipts (unknown tokens add nothing)."""
    calls = tokens = 0
    for primitive in run_ids:
        for receipt in sorted((directory / primitive / "receipts").glob("*.json")):
            row = tc.read(receipt)
            if row.get("engine") == "llm":
                calls += 1
                tokens += int((row.get("usage") or {}).get("input_tokens") or 0)
    return calls, tokens


def main(argv: list[str] | None = None) -> int:
    import os

    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--freeze", action="store_true")
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--unit", choices=sorted(UNITS), required=True)
    parser.add_argument("--run-spec", type=Path, action="append", default=[])
    parser.add_argument("--states", type=Path)
    parser.add_argument("--paraphrases", type=Path)
    parser.add_argument("--reviewed", action="store_true")
    parser.add_argument("--quota-live", action="store_true", help="user-approved WHAM lookup")
    args = parser.parse_args(argv)
    if args.freeze:
        if not (args.reviewed and args.run_spec and args.states):
            parser.error("--freeze needs --run-spec, --states and --reviewed")
        freeze(args.unit, args.run_spec, args.states, args.paraphrases)
        return 0
    if args.preflight:
        preflight(args.unit)
        print(f"{args.unit}: frozen inputs intact; no credential read")
        return 0
    if not args.reviewed:
        parser.error("--execute requires --reviewed")
    return asyncio.run(execute(args.unit, quota_live=args.quota_live))


if __name__ == "__main__":
    raise SystemExit(main())
