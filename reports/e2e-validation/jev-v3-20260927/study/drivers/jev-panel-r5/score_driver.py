"""Private P-track driver for Score-S selection (U0b selection, U4, U5s, X2).

  --freeze --unit U --run-spec F --pools P [--pools Q] [--states S]
           [--tolerance-freeze score-tolerance-freeze.json] --reviewed
  --preflight --unit U
  --execute --unit U --reviewed [--quota-live]

``score_selection.dispatch_selection`` (PR head) owns the call order, both
presentation orders, bounded concurrency, per-call timeouts and the §4.2
replacement rule; this driver passes the run-spec's ``max_concurrency=4`` and
``timeouts`` and builds the three selectors. The Jev selector always receives
``sum_tolerance`` and ``score_tolerance`` as explicit arguments: U0b uses 0.05,
later units the frozen ``score-tolerance-freeze.json``. Before any dispatch the
unit runs ``check_selector_tolerances.py`` against this driver's own selector
factory (:func:`frozen_selectors`), offline and without a credential.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import track_common as tc  # noqa: E402

LOCAL_FILES = (
    "score_driver.py",
    "track_common.py",
    "run_guards.py",
    "source_pin.py",
    "source-pin.json",
    "check_selector_tolerances.py",
)
UNITS = {
    "U0b": "geode-jev-score-bestof-admission-",
    "U4": "geode-jev-score-bestof-controlled-",
    "U5s": "geode-jev-score-bestof-selection-",
    "X2": "geode-jev-external-m2w-score-",
}
SUM_TOLERANCE = 0.025
U0B_SCORE_TOLERANCE = 0.05
MAX_CONCURRENCY = 4
TIMEOUTS = {"llm": 180.0, "jev": 60.0}
SELECTOR_NAMES = ("astra_pointwise", "jev_pointwise", "astra_listwise")
CONTEXT_ENV = "JEV_SCORE_UNIT_FREEZE"


def phase_dir(unit: str) -> Path:
    return HERE / unit.lower()


def driver_sha() -> str:
    return tc.sha(HERE / "score_driver.py")


def tolerances_for(unit: str, freeze_file: Path | None) -> dict[str, float]:
    """U0b: the §4.1 ceiling 0.05; later units: the frozen value (rule range 0.03-0.05)."""
    if unit == "U0b":
        if freeze_file is not None:
            raise ValueError("U0b runs before the score_tolerance freeze and takes 0.05")
        return {"sum_tolerance": SUM_TOLERANCE, "score_tolerance": U0B_SCORE_TOLERANCE}
    if freeze_file is None:
        raise ValueError(f"{unit} needs score-tolerance-freeze.json")
    document = tc.read(freeze_file)
    score = document.get("score_tolerance")
    total = document.get("sum_tolerance", SUM_TOLERANCE)
    if not (isinstance(score, float) and 0.03 <= score <= 0.05 and total == SUM_TOLERANCE):
        raise ValueError("score-tolerance-freeze.json is outside the §4.1 rule")
    return {"sum_tolerance": float(total), "score_tolerance": float(score)}


def build_selectors(tolerances: dict[str, float], *, astra: Any, jev: Any) -> list[Any]:
    """The run's selectors; the Jev bounds are always explicit (defaults are the strict 1e-5)."""
    from evals.benchmarks.score_selection import ListwiseSelector, PointwiseSelector

    return [
        PointwiseSelector(SELECTOR_NAMES[0], "llm", astra),
        PointwiseSelector(
            SELECTOR_NAMES[1],
            "jev",
            jev,
            sum_tolerance=tolerances["sum_tolerance"],
            score_tolerance=tolerances["score_tolerance"],
        ),
        ListwiseSelector(SELECTOR_NAMES[2]),
    ]


def frozen_selectors() -> list[Any]:
    """Zero-argument factory for ``check_selector_tolerances.py --selectors``; offline backends."""
    from core.llm.adapters.typesafe import SystemOneAdapter
    from pydantic import SecretStr

    tolerances = tc.read(Path(os.environ[CONTEXT_ENV]))["tolerances"]
    offline = SystemOneAdapter("typesafe", SecretStr("tolerance-check-offline"))
    return build_selectors(tolerances, astra=object(), jev=offline)


def load_pools(paths: list[Path], states: Path | None) -> list[Any]:
    from evals.benchmarks.score_selection import load_pools as library_load

    pools = [pool for path in paths for pool in library_load(path, states_path=states)]
    if len({pool.pool_id for pool in pools}) != len(pools):
        raise ValueError("pool ids repeat across pool files")
    return pools


def ordered(pools: list[Any], ids: list[str]) -> list[Any]:
    by_id = {pool.pool_id: pool for pool in pools}
    if set(by_id) < set(ids) or any(pool_id not in by_id for pool_id in ids):
        raise ValueError("the pool files lack a frozen workload")
    return [by_id[pool_id] for pool_id in ids]


def build_cells(
    pools: list[Any], tolerances: dict[str, float], source: Path, revision: str
) -> list[dict[str, Any]]:
    from evals.benchmarks.score_selection import ORDERS, frozen_pool_sha256, public_pool_sha256

    verifier = tc.sha(source / "evals/benchmarks/decision_candidate.py")
    cells = []
    for pool in pools:
        for name in SELECTOR_NAMES:
            engine = "jev" if name.startswith("jev") else "llm"
            for order in ORDERS:
                policy = {
                    "selector": name,
                    "route": tc.JEV_ROUTE if engine == "jev" else tc.ASTRA_ROUTE,
                    "order": order,
                    "max_concurrency": MAX_CONCURRENCY,
                    "timeout_s": TIMEOUTS[engine],
                    "tolerances": tolerances if engine == "jev" else "not-applicable",
                    "llm_max_retries": 1,
                    "source_revision": revision,
                }
                cells.append(
                    {
                        "index": len(cells),
                        "pool_id": pool.pool_id,
                        "kind": pool.kind,
                        "selector": name,
                        "order": order,
                        **tc.cell_digests(
                            policy,
                            case_sha256=public_pool_sha256(pool),
                            task_checksum=frozen_pool_sha256(pool),
                            verifier_sha256=verifier,
                        ),
                    }
                )
    return cells


def freeze(
    unit: str,
    spec_path: Path,
    pool_paths: list[Path],
    states: Path | None,
    tolerance_file: Path | None,
) -> dict[str, Any]:
    import source_pin
    from scripts.eval.contract import validate_run_spec

    source, revision = tc.pinned_source()
    if source_pin.clean_revision(source) != revision:
        raise ValueError("pinned checkout moved")
    spec = validate_run_spec(spec_path)
    ids = tc.check_spec(
        spec,
        prefix=UNITS[unit],
        revision=revision,
        driver_sha256=driver_sha(),
        max_concurrency=MAX_CONCURRENCY,
    )
    tolerances = tolerances_for(unit, tolerance_file)
    if unit != "U0b":
        from score_main_analysis import tolerance_authority

        assert tolerance_file is not None
        tolerance_authority(tolerance_file)
        if tc.sha(HERE / "score_main_analysis.py") not in spec["study"]["analysis_plan"]:
            raise ValueError("freeze the Score analysis entry SHA before main calls")
    pools = ordered(load_pools(pool_paths, states), ids)
    directory = phase_dir(unit)
    directory.mkdir(mode=0o700)
    copy = directory / "run-spec.json"
    tc.write_new(copy, spec_path.read_text(encoding="utf-8"))
    tolerance_copy = directory / "score-tolerance.json"
    tc.write_new(
        tolerance_copy,
        {
            **tolerances,
            "unit": unit,
            "source": str(tolerance_file) if tolerance_file else "U0b rule ceiling",
        },
    )
    inputs = [
        copy,
        tolerance_copy,
        *(p.resolve() for p in pool_paths),
        *(HERE / name for name in LOCAL_FILES),
    ]
    inputs += [p.resolve() for p in (states, tolerance_file) if p is not None]
    if unit != "U0b":
        inputs.append(HERE / "score_main_analysis.py")
    inputs += [
        source / "evals/benchmarks/score_selection.py",
        source / "evals/benchmarks/decision_candidate.py",
    ]
    record = {
        "schema": "jev-v3.score-freeze@1",
        "unit": unit,
        "run_id": spec["run_id"],
        "frozen_at": tc.now(),
        "source_revision": revision,
        "pools": [str(p.resolve()) for p in pool_paths],
        "states": str(states.resolve()) if states else None,
        "workload_ids": ids,
        "selectors": list(SELECTOR_NAMES),
        "tolerances": tolerances,
        "max_concurrency": MAX_CONCURRENCY,
        "timeouts": TIMEOUTS,
        "cells": build_cells(pools, tolerances, source, revision),
        "planned_astra_call_cap": spec["reproduction"]["execution"]["budget"]["limit"],
        "planned_jev_calls": 2 * len(pools),
        "driver_sha256": driver_sha(),
        "sha256": tc.bound_inputs(inputs),
    }
    tc.write_new(directory / "freeze.json", record)
    print(f"{unit}: frozen {len(pools)} pools x 3 selectors x 2 orders; no model call")
    return record


def preflight(unit: str) -> tuple[dict[str, Any], list[Any]]:
    import source_pin

    source, revision = tc.pinned_source()
    frozen = tc.read(phase_dir(unit) / "freeze.json")
    if (
        frozen["unit"] != unit
        or frozen["source_revision"] != revision
        or source_pin.clean_revision(source) != revision
    ):
        raise ValueError(f"{unit}: freeze belongs to another unit or source")
    tc.check_bound(frozen["sha256"])
    states = Path(frozen["states"]) if frozen["states"] else None
    pools = ordered(load_pools([Path(p) for p in frozen["pools"]], states), frozen["workload_ids"])
    if build_cells(pools, frozen["tolerances"], source, revision) != frozen["cells"]:
        raise ValueError(f"{unit}: frozen cells changed")
    return frozen, pools


def check_tolerances(unit: str, frozen: dict[str, Any], runner: Any = subprocess.run) -> bool:
    """``check_selector_tolerances.py`` on this driver's factory, isolated in a child process."""
    source, _ = tc.pinned_source()
    directory = phase_dir(unit)
    command = [
        sys.executable,
        "-B",
        str(HERE / "check_selector_tolerances.py"),
        "--source",
        str(source),
        "--freeze",
        str(directory / "score-tolerance.json"),
        "--selectors",
        "score_driver:frozen_selectors",
    ]
    for pool in frozen["pools"]:
        command += ["--pools", pool]
    if frozen["states"]:
        command += ["--states", frozen["states"]]
    env = {
        key: value for key, value in os.environ.items() if key in {"PATH", "HOME", "TMPDIR", "LANG"}
    }
    env.update(
        PYTHONPATH=os.pathsep.join([str(source), str(HERE)]),
        **{CONTEXT_ENV: str(directory / "freeze.json")},
    )
    result = runner(command, env=env, capture_output=True, text=True, timeout=300, cwd=HERE)
    tc.write_new(
        directory / "tolerance-check.json",
        {"exit_code": result.returncode, "stdout": result.stdout[-20000:]},
    )
    return result.returncode == 0


def settle_jev(
    ledger: Any,
    run_id: str,
    reservation: str,
    records: list[dict[str, Any]],
    started: dict[tuple[str, str], int] | None = None,
) -> dict[str, Any]:
    """Settle observed Jev calls; replaced attempts retain unknown token counts."""
    calls = []
    accounted: dict[tuple[str, str], int] = {}
    for record in records:
        entry = record["selectors"].get(SELECTOR_NAMES[1]) or {}
        for order, result in entry.get("orders", {}).items():
            key = (record["pool_id"], order)
            # A guard refusal is a retained infrastructure observation, not a
            # dispatched Jev call. Do not reserve usage for that synthetic row.
            if started is not None and started.get((record["pool_id"], order), 0) == 0:
                continue
            for index, _ in enumerate(result.get("replaced_attempts") or []):
                calls.append(
                    {
                        "call_id": f"{record['pool_id']}:{order}:replaced{index}",
                        "input_tokens": None,
                    }
                )
                accounted[key] = accounted.get(key, 0) + 1
            if started is not None and started.get((record["pool_id"], order), 0) <= len(
                result.get("replaced_attempts") or []
            ):
                continue
            usage = result.get("usage") or {}
            tokens = usage.get("input_tokens") if isinstance(usage, dict) else None
            calls.append(
                {
                    "call_id": f"{record['pool_id']}:{order}",
                    "input_tokens": tokens if isinstance(tokens, int) else None,
                }
            )
            accounted[key] = accounted.get(key, 0) + 1
    if started is not None:
        # TaskGroup exceptions/cancellation may prevent native records from
        # returning. Every started call still consumes an unknown amount; keep
        # its reserve instead of releasing it as a fabricated zero-call result.
        for (pool_id, order), count in started.items():
            for index in range(accounted.get((pool_id, order), 0), count):
                calls.append(
                    {"call_id": f"{pool_id}:{order}:unrecorded{index}", "input_tokens": None}
                )
    return ledger.settle(reservation, calls)


class ControlledSelector:
    """Delegate native selection unchanged after the existing host guard.

    The native dispatcher still owns concurrency, timeout and replacements. This
    hook is reached for replacements too. A refusal uses its nonreplaceable
    harness-error path so incomplete evidence cannot become a wrong-answer score.
    """

    def __init__(self, selector: Any, control: Any, astra_cap: int) -> None:
        self.selector, self.control, self.astra_cap = selector, control, astra_cap
        self.started: dict[tuple[str, str], int] = {}

    def __getattr__(self, name: str) -> Any:
        return getattr(self.selector, name)

    async def run(self, pool: Any, order: str) -> Any:
        from evals.benchmarks.score_selection import CallFailureError

        engine = self.selector.engine or "llm"
        if engine == "llm" and self.control.astra_calls >= self.astra_cap:
            self.control.stopped = "astra_budget_exhausted"
        reason = self.control.before_call(engine)
        if reason is not None:
            raise CallFailureError("harness_error", reason)
        key = (pool.pool_id, order)
        self.started[key] = self.started.get(key, 0) + 1
        return await self.selector.run(pool, order)


async def execute(unit: str, *, quota_live: bool, engines: Any = None, checker: Any = None) -> int:
    """Dispatch one frozen unit; ``engines``/``checker`` are injected only by mock tests."""
    import httpx
    from evals.benchmarks.score_selection import SelectionStoppedError, dispatch_selection

    frozen, pools = preflight(unit)
    directory = phase_dir(unit)
    admission = tc.admit(
        directory,
        unit=unit,
        run_id=frozen["run_id"],
        lock_mode="panel-unit",
        planned_astra=frozen["planned_astra_call_cap"],
        planned_jev=frozen["planned_jev_calls"],
        required_margin_s=int(
            len(frozen["cells"]) * max(TIMEOUTS.values()) / MAX_CONCURRENCY + tc.AUTH_MARGIN_SLACK_S
        ),
        quota_live=quota_live,
    )
    if admission is None:
        return 3
    records: list[dict[str, Any]] = []
    stop: str | None = None
    secrets: list[str] = []
    control = tc.CallControl(admission, reader=tc.live_snapshot if quota_live else None)
    selectors: list[Any] = []
    try:
        tc.pin_runtime_settings()
        if not (checker or check_tolerances)(unit, frozen):
            tc.stop_unit(
                directory, "tolerance_check_failed", "check_selector_tolerances.py did not pass"
            )
            stop = "tolerance_check_failed"
            return 3
        if engines is None:
            from core.llm.adapters.typesafe import SystemOneAdapter

            key = tc.load_typesafe_key()
            client = httpx.AsyncClient(timeout=TIMEOUTS["jev"] + 10)
            astra, jev = tc.astra_adapter(), SystemOneAdapter("typesafe", key, client=client)
        else:
            astra, jev, key, client = engines
        secrets.append(key.get_secret_value())
        selectors = [
            ControlledSelector(s, control, frozen["planned_astra_call_cap"])
            for s in build_selectors(frozen["tolerances"], astra=astra, jev=jev)
        ]
        reservation = admission.ledger.reserve(frozen["run_id"], 2 * frozen["planned_jev_calls"])
        timings: list[dict[str, Any]] = []
        try:
            records = await dispatch_selection(
                pools,
                selectors,
                max_concurrency=frozen["max_concurrency"],
                timeouts=frozen["timeouts"],
                timings=timings,
            )
        except SelectionStoppedError as error:
            records, stop = error.records, control.stopped or error.reason
            tc.stop_unit(directory, stop, "native Score dispatch stopped")
        finally:
            if engines is None:
                await client.aclose()
            settlement = settle_jev(
                admission.ledger, frozen["run_id"], reservation, records, selectors[1].started
            )
        tc.write_new(
            directory / "dispatch-records.jsonl",
            "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in records),
        )
        tc.write_new(directory / "timings.json", timings)
        tc.block_receipt(
            admission,
            block_id=unit,
            lock_mode="panel-unit",
            source_revision=frozen["source_revision"],
            freeze_sha256=tc.sha(directory / "freeze.json"),
            extra={
                "planned_calls": len(frozen["cells"]),
                "records": len(records),
                "stop_reason": stop,
                "guard_stop_reason": control.stopped,
                "started_astra_calls": sum(
                    sum(s.started.values()) for s in selectors if s.engine != "jev"
                ),
                "started_jev_calls": sum(selectors[1].started.values()),
                "tolerances": frozen["tolerances"],
                "jev_reservation_id": reservation,
                "jev_calls_settled": len(settlement.get("calls", [])),
                "jev_estimate_usd": settlement.get("estimate_usd"),
                "jev_reserve_usd": settlement.get("reserve_usd"),
            },
        )
    finally:
        calls, tokens = astra_usage(records)
        if selectors:
            calls = sum(sum(s.started.values()) for s in selectors if s.engine != "jev")
        admission.close(astra_calls=calls, astra_input_tokens=tokens)
        tc.assert_no_secret(directory, secrets)
    print(json.dumps({"unit": unit, "records": len(records), "stop_reason": stop}))
    return 0 if stop is None else 1


def astra_usage(records: list[dict[str, Any]]) -> tuple[int, int]:
    calls = tokens = 0
    for record in records:
        for name, entry in record["selectors"].items():
            if name == SELECTOR_NAMES[1]:
                continue
            for result in entry["orders"].values():
                calls += 1 + len(result.get("replaced_attempts") or [])
                usage = result.get("usage")
                tokens += int(usage.get("input_tokens") or 0) if isinstance(usage, dict) else 0
    return calls, tokens


def main(argv: list[str] | None = None) -> int:
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--freeze", action="store_true")
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--unit", choices=sorted(UNITS), required=True)
    parser.add_argument("--run-spec", type=Path)
    parser.add_argument("--pools", type=Path, action="append", default=[])
    parser.add_argument("--states", type=Path)
    parser.add_argument("--tolerance-freeze", type=Path)
    parser.add_argument("--reviewed", action="store_true")
    parser.add_argument("--quota-live", action="store_true", help="user-approved WHAM lookup")
    args = parser.parse_args(argv)
    if args.freeze:
        if not (args.reviewed and args.run_spec and args.pools):
            parser.error("--freeze needs --run-spec, --pools and --reviewed")
        freeze(args.unit, args.run_spec, args.pools, args.states, args.tolerance_freeze)
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
