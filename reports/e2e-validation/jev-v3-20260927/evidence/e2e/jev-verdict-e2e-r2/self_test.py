"""Model-free checks of the paired dispatcher, host guards and slot matrix.

``runner.py --self-test`` runs every scenario; pytest runs them one by one. Mock
children replace Harbor trials: no Docker, Harbor run, credential or model call.
Scenarios that need the pinned GEODE source (Jev ledger, barrier agent) skip when
it is not importable.
"""

from __future__ import annotations

import asyncio
import base64
import contextlib
import json
import sys
import tempfile
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from paired_dispatch import (  # noqa: E402
    PairedDispatcher,
    Slot,
    SlotMatrixError,
    load_slots,
    parse_utc,
    utc,
)
from run_guards import (  # noqa: E402
    QUOTA_COLUMNS,
    AccountClaims,
    ExecutionLock,
    QuotaLedger,
    QuotaSnapshot,
    ScheduleOverlapError,
    account_fields,
    account_refusal,
    latest_snapshot,
    read_account_claims,
    record_snapshot,
)
from slot_guards import AccountGuard, JevGuard, LockGuard, QuotaGuard, StopFileGuard  # noqa: E402

G0_FP = "anonymous-account-02"
EXPECTED_SLOTS = {"U0d": 2, "U0e": 1, "U0f": 2, "U7r0": 12, "U7r1": 12, "U8c": 18, "U8n": 18}


class Skip(Exception):
    """A scenario whose optional dependency is absent."""


@contextlib.contextmanager
def scratch() -> Iterator[Path]:
    with tempfile.TemporaryDirectory(prefix="jev3-selftest-") as name:
        yield Path(name)


def make_slots(unit: str, count: int, arms: tuple[str, ...] = ("A", "B")) -> list[Slot]:
    slots = []
    for index in range(1, count + 1):
        order = arms if index % 2 else tuple(reversed(arms))
        slots.append(
            Slot(
                unit,
                f"{unit}-s{index:02d}",
                index,
                f"task-{index}",
                "natural",
                0,
                tuple(sorted(arms)),
                order,
            )
        )
    return slots


@dataclass
class ArmPlan:
    duration: float = 0.05
    exit_code: int = 0
    hang: bool = False
    agent_offset_s: float | None = 0.01
    valid: bool = True
    jev_calls: list[dict[str, Any]] = field(default_factory=list)


class FakeHandle:
    def __init__(self, plan: ArmPlan, events: list[tuple[str, ...]], key: tuple[str, str]) -> None:
        self.plan, self.events, self.key, self.stopped = plan, events, key, False
        self._stop = asyncio.Event()

    async def wait(self) -> int:
        if self.plan.hang:
            await self._stop.wait()
        else:
            await asyncio.sleep(self.plan.duration)
        self.events.append(("exit", *self.key))
        return self.plan.exit_code

    async def stop(self) -> str | None:
        self.stopped = True
        self._stop.set()
        self.events.append(("stop", *self.key))
        return None


class FakeDriver:
    """Mock trials: no process; each launch returns at once and runs in the loop."""

    def __init__(
        self, plans: dict[tuple[str, str], ArmPlan], *, advance: Callable[[], None] | None = None
    ) -> None:
        self.plans, self.advance = plans, advance
        self.events: list[tuple[str, ...]] = []
        self.handles: dict[tuple[str, str], FakeHandle] = {}

    def prepare(self, slot: Slot, arm: str) -> dict[str, Any]:
        self.events.append(("prepare", slot.slot_id, arm))
        return {"arm": arm}

    async def launch(self, slot: Slot, arm: str, prepared: Any) -> FakeHandle:
        if self.advance is not None:
            self.advance()
        key = (slot.slot_id, arm)
        self.events.append(("launch", *key))
        handle = FakeHandle(self.plans.get(key, ArmPlan()), self.events, key)
        self.handles[key] = handle
        return handle

    def release(self, slot: Slot, arm: str, prepared: Any) -> str | None:
        self.events.append(("release", slot.slot_id, arm))
        return None


def fake_collect(driver: FakeDriver) -> Callable[..., Any]:
    async def collect(slot: Slot, run: Any) -> dict[str, Any]:
        plan = driver.plans.get((slot.slot_id, run.arm), ArmPlan())
        driver.events.append(("collect", slot.slot_id, run.arm))
        launched = parse_utc(run.host_launch_utc)
        valid = plan.valid and run.error is None and run.exit_code == 0
        return {
            "validity": "valid" if valid else "invalid",
            "outcome": "passed" if valid else "unknown",
            "failure_class": None if valid else (run.error or "fake_invalid"),
            "agent_start_utc": None
            if plan.agent_offset_s is None or launched is None
            else utc(launched + plan.agent_offset_s),
            "jev_calls": plan.jev_calls,
        }

    return collect


def dispatch(slots: list[Slot], driver: FakeDriver, **kwargs: Any) -> Any:
    dispatcher = PairedDispatcher(driver=driver, collect=fake_collect(driver), **kwargs)
    return asyncio.run(dispatcher.run(slots))


# --- scenarios ---------------------------------------------------------------------


def scenario_concurrent_launch() -> None:
    slots = make_slots("U7r0", 2)
    plans = {
        ("U7r0-s01", "A"): ArmPlan(duration=0.20, agent_offset_s=0.02),
        ("U7r0-s01", "B"): ArmPlan(duration=0.30, agent_offset_s=0.07),
    }
    driver = FakeDriver(plans)
    report = dispatch(slots, driver)
    events = driver.events
    first = [e for e in events if e[1] == "U7r0-s01"]
    launches = [i for i, e in enumerate(first) if e[0] == "launch"]
    exits = [i for i, e in enumerate(first) if e[0] == "exit"]
    assert max(launches) < min(exits), "both arms must be running before either exits"
    last_s01 = max(i for i, e in enumerate(events) if e[1] == "U7r0-s01")
    first_s02 = min(i for i, e in enumerate(events) if e[1] == "U7r0-s02")
    assert last_s01 < first_s02, "next slot started before the previous slot was collected"
    assert [e[0] for e in events if e[1] == "U7r0-s01"][-2:] == ["collect", "collect"]
    one = report.slots[0]
    assert report.complete and len(report.slots) == 2
    assert one.launch_skew_s is not None and one.launch_skew_s < 0.5
    assert one.agent_start_skew_s is not None and abs(one.agent_start_skew_s - 0.05) < 0.02
    assert one.pair_sync is True and one.concurrent == {"A": 1, "B": 1}
    assert one.agent_start_order == ("A", "B")
    assert [run.position for run in one.runs.values()] == [0, 1]
    second = report.slots[1]
    assert second.slot.launch_order == ("B", "A") and second.runs["B"].position == 0


def scenario_three_arms() -> None:
    slots = [Slot("U7r0", "U7r0-s01", 1, "task", "natural", 0, ("A", "B", "C"), ("A", "B", "C"))]
    plans = {
        ("U7r0-s01", arm): ArmPlan(duration=0.2, agent_offset_s=0.02 + 0.02 * i)
        for i, arm in enumerate("ABC")
    }
    report = dispatch(slots, FakeDriver(plans))
    slot = report.slots[0]
    assert slot.concurrent == {"A": 2, "B": 2, "C": 2} and slot.pair_sync is True
    assert abs(slot.agent_start_skew_s - 0.04) < 0.02


def scenario_launch_skew_stops_unit() -> None:
    clock = [1000.0]

    def advance() -> None:
        clock[0] += 1.2

    slots = make_slots("U8c", 2)
    driver = FakeDriver({}, advance=advance)
    report = dispatch(slots, driver, monotonic=lambda: clock[0])
    assert len(report.slots) == 1, "a defective launch must stop the unit after its slot"
    assert report.stop is not None and report.stop.failure_class == "dispatch_skew_exceeded"
    rows = report.slots[0].rows
    assert all(
        row["validity"] == "invalid" and row["failure_class"] == "dispatch_skew_exceeded"
        for row in rows.values()
    )
    assert not any(e[1] == "U8c-s02" for e in driver.events)


def scenario_agent_skew_marks_pair_sync_only() -> None:
    slots = make_slots("U7r0", 2)
    plans = {
        ("U7r0-s01", "A"): ArmPlan(agent_offset_s=5.0),
        ("U7r0-s01", "B"): ArmPlan(agent_offset_s=45.0),
    }
    report = dispatch(slots, FakeDriver(plans))
    assert report.complete and len(report.slots) == 2
    assert report.slots[0].pair_sync is False and report.slots[0].agent_start_skew_s > 30
    assert report.summary()["pair_sync_false"] == 1


def scenario_invalid_arm_keeps_sibling_and_stops() -> None:
    slots = make_slots("U7r0", 2)
    plans = {
        ("U7r0-s01", "A"): ArmPlan(duration=0.4),
        ("U7r0-s01", "B"): ArmPlan(duration=0.05, valid=False),
    }
    driver = FakeDriver(plans)
    report = dispatch(slots, driver)
    assert report.stop is not None and report.stop.failure_class == "infrastructure_invalid_arm"
    assert (
        report.slots[0].runs["A"].exit_code == 0
        and report.slots[0].rows["A"]["validity"] == "valid"
    )
    assert not driver.handles[("U7r0-s01", "A")].stopped, "a sibling must never be cancelled"
    assert not any(e[1] == "U7r0-s02" for e in driver.events)


def scenario_watchdog_stops_hung_arm() -> None:
    slots = make_slots("U8n", 1)
    plans = {("U8n-s01", "A"): ArmPlan(hang=True), ("U8n-s01", "B"): ArmPlan(duration=0.05)}
    driver = FakeDriver(plans)
    report = dispatch(slots, driver, watchdog_s=0.3)
    run = report.slots[0].runs["A"]
    assert run.error == "watchdog_timeout" and driver.handles[("U8n-s01", "A")].stopped
    assert report.slots[0].rows["A"]["validity"] == "invalid"
    assert report.stop is not None


def scenario_prepare_failure_launches_nothing() -> None:
    class Failing(FakeDriver):
        def prepare(self, slot: Slot, arm: str) -> dict[str, Any]:
            if arm == "B":
                raise OSError("secret unavailable")
            return super().prepare(slot, arm)

    driver = Failing({})
    report = dispatch(make_slots("U8c", 1), driver)
    assert report.stop is not None and report.stop.failure_class == "dispatcher_prepare"
    assert not any(e[0] == "launch" for e in driver.events)
    assert ("release", "U8c-s01", "A") in driver.events


def scenario_execution_lock() -> None:
    with scratch() as root:
        first = ExecutionLock(
            root, mode="e2e-slot", run_id="geode-jev-verdict-e2e-injection-20260927"
        )
        second = ExecutionLock(
            root, mode="panel-unit", run_id="geode-jev-verdict-panel-test-choice-20260927"
        )
        first.acquire()
        try:
            second.acquire()
        except ScheduleOverlapError as error:
            assert error.failure_class == "schedule_overlap"
            assert error.holder["mode"] == "e2e-slot"
        else:
            raise AssertionError("two tracks held the execution lock")
        guard = LockGuard(first)
        slot = make_slots("U8c", 1)[0]
        assert guard.before_slot(slot) is None
        holder = json.loads((root / ".execution-lock").read_text())
        (root / ".execution-lock").write_text(json.dumps({**holder, "token": "someone-else"}))
        decision = guard.before_slot(slot)
        assert decision is not None and decision.failure_class == "schedule_overlap"
        first.release()
        second.acquire()
        second.release()
        events = [
            json.loads(line)["event"]
            for line in (root / ".execution-lock.log.jsonl").read_text().splitlines()
        ]
        assert events == ["acquire", "refused", "lost", "release", "acquire", "release"]
        try:
            ExecutionLock(root, mode="other", run_id="x")
        except ValueError:
            pass
        else:
            raise AssertionError("unknown track mode accepted")


def scenario_lock_lost_mid_unit() -> None:
    with scratch() as root:
        lock = ExecutionLock(
            root, mode="e2e-slot", run_id="geode-jev-verdict-e2e-natural-r0-20260927"
        )
        lock.acquire()
        driver = FakeDriver({})

        def tamper(report: Any) -> None:
            (root / ".execution-lock").unlink()

        dispatcher = PairedDispatcher(
            driver=driver, collect=fake_collect(driver), guards=[LockGuard(lock)], on_slot=tamper
        )
        report = asyncio.run(dispatcher.run(make_slots("U7r0", 3)))
        lock.release()
        assert report.stop is not None and report.stop.failure_class == "schedule_overlap"
        assert len(report.slots) == 1 and report.stopped_before == "U7r0-s02"


def _jwt(claims: dict[str, Any]) -> str:
    body = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
    return f"eyJhbGciOiJub25lIn0.{body}.signature"


def scenario_account_claims_and_guard() -> None:
    now = time.time()
    with scratch() as root:
        auth = root / "auth.json"
        secret = "synthetic-access-token-body"
        claims = {
            "exp": int(now + 10 * 86400),
            "https://api.openai.com/auth": {"chatgpt_plan_type": "prolite"},
            "x": secret,
        }
        auth.write_text(
            json.dumps(
                {
                    "tokens": {
                        "access_token": _jwt(claims),
                        "account_id": "acct-synthetic",
                        "refresh_token": "r",
                    }
                }
            )
        )
        read = read_account_claims(auth)
        assert read.plan == "prolite" and read.fp12 is not None and len(read.fp12) == 12
        assert secret not in repr(read) and "acct-synthetic" not in repr(read)
    good = AccountClaims(G0_FP, "prolite", now + 10 * 86400)
    fields = account_fields(good, now=now)
    assert (
        fields["account_matches_g0"] is True
        and account_refusal(fields, required_margin_s=3600) is None
    )
    assert (
        account_refusal(
            account_fields(AccountClaims("0" * 12, "prolite", now + 9e5), now=now),
            required_margin_s=1,
        )
        == "account_changed"
    )
    assert (
        account_refusal(
            account_fields(AccountClaims(G0_FP, "plus", now + 9e5), now=now), required_margin_s=1
        )
        == "account_changed"
    )
    assert (
        account_refusal(
            account_fields(AccountClaims(G0_FP, "prolite", now + 100), now=now),
            required_margin_s=3600,
        )
        == "auth_expiry_margin"
    )
    assert (
        account_refusal(
            account_fields(AccountClaims(None, None, None), now=now), required_margin_s=1
        )
        == "account_unreadable"
    )
    readings = iter([good, AccountClaims("f" * 12, "prolite", now + 9e5)])
    guard = AccountGuard(
        fields,
        make_slots("U8c", 3),
        reader=lambda: next(readings),
        slot_bound_s=1050,
        clock=lambda: now,
    )
    driver = FakeDriver({})
    report = asyncio.run(
        PairedDispatcher(driver=driver, collect=fake_collect(driver), guards=[guard]).run(
            make_slots("U8c", 3)
        )
    )
    assert report.stopped_before == "U8c-s02" and report.stop.failure_class == "account_changed"
    assert guard.fields["U8c-s01"]["codex_account_fp12"] == G0_FP


def _ledger(root: Path) -> QuotaLedger:
    path = root / "quota-ledger.csv"
    g0 = [
        "G0",
        "2026-09-26 22:16",
        "G0",
        "51",
        "604800",
        "2026-10-01 04:10",
        G0_FP,
        "prolite",
        "true",
        "0",
        "0",
        "",
        "",
        "",
        "none",
        "U0a",
        "16",
        "",
        "calibrating",
        "g0",
    ]
    path.write_text(",".join(QUOTA_COLUMNS) + "\n" + ",".join(g0) + "\n")
    return QuotaLedger(path)


def scenario_quota_projection() -> None:
    fields = account_fields(AccountClaims(G0_FP, "prolite", time.time() + 9e5), now=time.time())
    with scratch() as root:
        ledger = _ledger(root)
        start = ledger.start_decision(
            unit="U0d",
            planned_astra_calls=40,
            snapshot=QuotaSnapshot(51.0, 604800, None, "t"),
            account=fields,
            checkpoint_id="U0d-start",
        )
        assert start["decision"] == "calibrating" and start["projected_end_pct"] == "51.0"
        assert (
            ledger.start_decision(
                unit="U0d", planned_astra_calls=40, snapshot=None, account=fields, checkpoint_id="x"
            )["decision"]
            == "no-snapshot"
        )
        ledger.end_record(
            unit="U0d",
            snapshot=QuotaSnapshot(52.0, None, None, "t"),
            start_used_pct=51.0,
            unit_astra_calls=100,
            unit_astra_input_tokens=1000,
            account=fields,
            checkpoint_id="U0d-end",
        )
        r, status = ledger.calibration()
        assert status == "provisional" and abs(r - 2.0) < 1e-9, (r, status)
        ledger.end_record(
            unit="U0a",
            snapshot=QuotaSnapshot(55.0, None, None, "t"),
            start_used_pct=52.0,
            unit_astra_calls=100,
            unit_astra_input_tokens=1000,
            account=fields,
            checkpoint_id="U0a-end",
        )
        r, status = ledger.calibration()
        assert status == "measured" and abs(r - 2.0) < 1e-9, (r, status)
        stop = ledger.start_decision(
            unit="U8c",
            planned_astra_calls=2000,
            snapshot=QuotaSnapshot(55.0, None, None, "t"),
            account=fields,
            checkpoint_id="U8c-start",
        )
        assert stop["decision"] == "pause-reset"
        go = ledger.start_decision(
            unit="U8c",
            planned_astra_calls=360,
            snapshot=QuotaSnapshot(55.0, None, None, "t"),
            account=fields,
            checkpoint_id="U8c-start",
        )
        assert go["decision"] == "start" and float(go["projected_end_pct"]) <= 90
        assert (
            ledger.in_unit_decision(QuotaSnapshot(95.0, None, None, "t"), unit="U4") == "quota_stop"
        )
        assert ledger.in_unit_decision(QuotaSnapshot(94.9, None, None, "t"), unit="U4") is None
        record_snapshot(
            ledger,
            QuotaSnapshot(60.0, 604800, "2026-10-01 04:10", "operator-status"),
            account=fields,
            checkpoint_id="S1",
        )
        assert latest_snapshot(ledger, max_age_s=3600).used_pct == 60.0
        assert latest_snapshot(ledger, max_age_s=-1) is None
        bad = root / "bad.csv"
        bad.write_text("checkpoint_id,time_kst\n")
        try:
            QuotaLedger(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("ledger with changed columns accepted")
        guard = QuotaGuard(
            ledger, "U4", make_slots("U4", 4), 336, lambda: QuotaSnapshot(96.0, None, None, "t")
        )
        slots = make_slots("U4", 4)
        assert guard.before_slot(slots[0]) is None
        decision = guard.before_slot(slots[2])
        assert decision is not None and decision.failure_class == "quota_stop"
        assert QuotaGuard(ledger, "U8c", slots, 200, lambda: None).check_at is None


def scenario_operator_stop_file() -> None:
    with scratch() as root:
        guard = StopFileGuard(root)
        slot = make_slots("U8c", 1)[0]
        assert guard.before_slot(slot) is None
        (root / "STOP").write_text("stop\n")
        assert guard.before_slot(slot).failure_class == "operator_stop"


CANONICAL = (
    "slot_id",
    "dispatch_skew_s",
    "agent_start_skew_s",
    "pair_sync",
    "concurrent_trials",
    "external_account_usage",
)
DRAFT_NAMES = (
    "pair_launch_skew_s",
    "pair_agent_start_skew_s",
    "concurrent_trials_active",
    "same_account_external_usage",
)


def scenario_receipt_canonical_columns() -> None:
    report = dispatch(make_slots("U7r0", 1), FakeDriver({}))
    for arm in ("A", "B"):
        fields = report.slots[0].concurrency_fields(arm)
        assert all(name in fields for name in CANONICAL)
        assert not any(name in fields for name in DRAFT_NAMES), "Run draft aliases are not written"
        assert fields["external_account_usage"] == "unknown" and fields["concurrent_trials"] == 1
        assert fields["pair_sync"] is (fields["agent_start_skew_s"] <= 30)
        assert fields["slot_id"] == "U7r0-s01" and "overlapping_calls" not in fields
    summary = report.slots[0].summary()
    assert not any(name in summary for name in DRAFT_NAMES)


def scenario_slot_matrix(path: Path | None = None) -> None:
    path = path or HERE / "e2e-slots.jsonl"
    if not path.is_file():
        raise Skip("no e2e-slots.jsonl next to the runner")
    rows = [json.loads(line) for line in path.read_text().splitlines() if line]
    for unit, count in EXPECTED_SLOTS.items():
        if unit == "U0f":
            try:
                load_slots(rows, unit, arm_c=False)
            except SlotMatrixError:
                pass
            else:
                raise AssertionError("U0f ran without arm C")
            assert len(load_slots(rows, unit, arm_c=True)) == count
            continue
        slots = load_slots(rows, unit, arm_c=False)
        assert len(slots) == count and all(s.arms in (("A", "B"),) for s in slots), unit
    with_c = load_slots(rows, "U7r0", arm_c=True)
    assert [s.launch_order for s in with_c[:3]] == [
        ("A", "B", "C"),
        ("B", "C", "A"),
        ("C", "A", "B"),
    ]
    assert with_c[0].replay_preselected and with_c[0].replay_side("C") == "appendix"
    swapped = [dict(row) for row in rows]
    target = next(row for row in swapped if row["slot_id"] == "U8c-s02")
    target["launch_order"] = list(reversed(target["launch_order"]))
    try:
        load_slots(swapped, "U8c", arm_c=False)
    except SlotMatrixError:
        pass
    else:
        raise AssertionError("a changed launch order was accepted")
    moved = [dict(row) for row in rows]
    target = next(row for row in moved if row["slot_id"] == "U8n-s01")
    target["cell"] = "c1m1"
    try:
        load_slots(moved, "U8n", arm_c=False)
    except SlotMatrixError:
        pass
    else:
        raise AssertionError("a changed U8 cell rotation was accepted")


def scenario_jev_guard() -> None:
    try:
        from evals.benchmarks.jev_cost_ledger import JevCostLedger
    except ImportError as error:
        raise Skip("pinned GEODE source not importable") from error
    slots = make_slots("U8c", 2)
    cells = {(s.slot_id, arm): {"uses_jev": arm == "B"} for s in slots for arm in ("A", "B")}
    with scratch() as root:
        ledger = JevCostLedger.create(root / "ledger.jsonl")
        ledger.admit_unit("geode-jev-verdict-e2e-injection-20260927", 12)
        guard = JevGuard(
            ledger, "geode-jev-verdict-e2e-injection-20260927", cells, calls_per_trial=6
        )
        plans = {
            (s.slot_id, "B"): ArmPlan(
                jev_calls=[
                    {"call_id": f"{s.slot_id}-j1", "input_tokens": 2600},
                    {"call_id": None, "input_tokens": None},
                ]
            )
            for s in slots
        }
        driver = FakeDriver(plans)
        report = asyncio.run(
            PairedDispatcher(driver=driver, collect=fake_collect(driver), guards=[guard]).run(slots)
        )
        assert report.complete and not guard.reservations
        settled = guard.settlements[("U8c-s01", "B")]
        assert settled["estimate_usd"] == "0.000109200" and settled["reserve_usd"] == "0.001050000"
        assert ("U8c-s01", "A") not in guard.settlements
    with scratch() as root:
        tight = JevCostLedger.create(
            root / "ledger.jsonl",
            cost_limit_usd="0.010000000",
            start_limit_usd="0.001000000",
            stop_limit_usd="0.005000000",
        )
        tight.admit_unit("u", 0, p95_input_tokens=0)
        guard = JevGuard(tight, "u", cells, calls_per_trial=6)
        plans = {("U8c-s01", "B"): ArmPlan(jev_calls=[{"call_id": "big", "input_tokens": 200_000}])}
        driver = FakeDriver(plans)
        report = asyncio.run(
            PairedDispatcher(driver=driver, collect=fake_collect(driver), guards=[guard]).run(slots)
        )
        assert report.stop is not None and report.stop.failure_class == "jev_budget_exhausted"
        assert len(report.slots) == 1
        refused = JevGuard(tight, "u", cells, calls_per_trial=6).before_slot(slots[1])
        assert refused is not None and refused.failure_class == "jev_budget_refused"


def scenario_barrier() -> None:
    try:
        from slot_agent import wait_for_peers
    except ImportError as error:
        raise Skip("pinned GEODE source not importable") from error
    with scratch() as root:

        async def both() -> list[dict[str, Any]]:
            return list(
                await asyncio.gather(
                    wait_for_peers(root, "A", ["B"], timeout_s=5, poll_s=0.01),
                    wait_for_peers(root, "B", ["A"], timeout_s=5, poll_s=0.01),
                )
            )

        receipts = asyncio.run(both())
        assert all(not r["timed_out"] for r in receipts)
    with scratch() as root:
        alone = asyncio.run(wait_for_peers(root, "A", ["B"], timeout_s=0.2, poll_s=0.01))
        assert alone["timed_out"] and alone["peers_ready"] == []
        assert json.loads((root / "A.json").read_text())["timed_out"] is True


SCENARIOS: dict[str, Callable[[], None]] = {
    name.removeprefix("scenario_"): value
    for name, value in dict(globals()).items()
    if name.startswith("scenario_") and callable(value)
}


def run() -> int:
    results: dict[str, str] = {}
    for name, scenario in SCENARIOS.items():
        try:
            scenario()
            results[name] = "pass"
        except Skip as skip:
            results[name] = f"skip: {skip}"
        except Exception as error:  # report every scenario, then fail
            results[name] = f"FAIL: {type(error).__name__}: {error}"
    failed = [name for name, status in results.items() if status.startswith("FAIL")]
    print(json.dumps({"scenarios": results, "failed": failed, "model_dispatches": 0}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(run())
