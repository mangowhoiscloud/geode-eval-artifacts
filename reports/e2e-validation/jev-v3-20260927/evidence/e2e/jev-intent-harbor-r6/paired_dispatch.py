"""Paired concurrent slot dispatch for the Jev v3 E track (05 v2 §2.4-§2.6).

Stdlib only. The runner injects every side effect: preparing and launching one
child process per arm, collecting a finished trial, and the guards that may stop
a unit. One slot launches all of its arms back to back in its frozen launch
order, lets each arm run under its own watchdog, and returns only after every
arm has exited and been collected (collection verifies container cleanup), so
the next slot never overlaps the previous one.

Rules applied here (05 v2 §2.4, §4.3):
* ``dispatch_skew_s`` (launch skew) > 1 s is a dispatcher defect: the slot's
  trials are marked infrastructure-invalid and the unit stops after the slot.
* ``agent_start_skew_s`` > 30 s only sets ``pair_sync=false``.
* Any infrastructure-invalid arm stops the unit after its siblings finish;
  siblings are never cancelled because of it.
* A guard may refuse the next slot (lock, account, quota, Jev budget, operator
  stop) or stop the unit after a slot.
"""

from __future__ import annotations

import asyncio
import json
import math
import time
from collections.abc import Awaitable, Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

LAUNCH_SKEW_LIMIT_S = 1.0
AGENT_SYNC_LIMIT_S = 30.0
BARRIER_TIMEOUT_S = 120.0
WATCHDOG_S = 930.0
ARM_LABELS = {"A": "llm", "B": "jev", "C": "cascade"}
# Receipt column names follow the coordinator list (the data tables' canonical columns).
EXTERNAL_USAGE = {
    "external_account_usage": "unknown",
    "external_usage_reason": "shared-account-video-session",
}
SLOT_KEYS = frozenset(
    {
        "unit",
        "slot_id",
        "slot_index",
        "task",
        "cell",
        "repetition",
        "arms",
        "launch_order",
        "replay_preselected",
        "replay_layout",
        "conditional_on_arm_c",
    }
)
OPTIONAL_SLOT_KEYS = frozenset({"note", "launch_order_if_c", "source"})
U8_CELLS = ("c1m0", "c0m1", "c1m1")
# Matrix rows that only preview the design; freeze and the public check refuse them.
PREVIEW_SOURCES = frozenset({"T+ preview", "option E placeholder"})
C_ROTATIONS = (("A", "B", "C"), ("B", "C", "A"), ("C", "A", "B"))


class SlotMatrixError(ValueError):
    """The frozen slot matrix breaks a pre-registered order or identity rule."""


@dataclass(frozen=True)
class Slot:
    """One (unit, task[, cell], repetition) slot with every compared arm."""

    unit: str
    slot_id: str
    slot_index: int
    task: str
    cell: str
    repetition: int
    arms: tuple[str, ...]
    launch_order: tuple[str, ...]
    replay_preselected: bool = False
    replay_layout: str | None = None
    source: str | None = None

    @property
    def workload_id(self) -> str:
        """Run-spec workload ID: the task for natural slots, ``task#cell`` otherwise."""
        return self.task if self.cell == "natural" else f"{self.task}#{self.cell}"

    def replay_side(self, arm: str) -> str | None:
        """Fixed replay side (A left, B right, C appendix) for a preselected slot only."""
        if not self.replay_preselected:
            return None
        return {"A": "left", "B": "right", "C": "appendix"}[arm]


def load_slots(rows: Iterable[Mapping[str, Any]], unit: str, *, arm_c: bool) -> list[Slot]:
    """Parse one unit's rows of ``e2e-slots.jsonl``; C joins only when approved.

    With arm C approved, a natural U7 slot uses its frozen ``launch_order_if_c``;
    U0f is C-only and is refused unless C is approved.
    """
    slots: list[Slot] = []
    for row in rows:
        if row.get("unit") != unit:
            continue
        keys = set(row)
        if not keys >= SLOT_KEYS or keys - SLOT_KEYS - OPTIONAL_SLOT_KEYS:
            raise SlotMatrixError(f"{row.get('slot_id')}: slot fields changed")
        arms = tuple(row["arms"])
        order = tuple(row["launch_order"])
        if row["conditional_on_arm_c"] and not arm_c:
            raise SlotMatrixError(f"{row['slot_id']}: arm C is not approved; unit is not run")
        if arm_c and unit.startswith("U7"):
            order = tuple(row.get("launch_order_if_c") or ())
            arms = tuple(sorted(order))
        slots.append(
            Slot(
                unit=unit,
                slot_id=str(row["slot_id"]),
                slot_index=int(row["slot_index"]),
                task=str(row["task"]),
                cell=str(row["cell"]),
                repetition=int(row["repetition"]),
                arms=arms,
                launch_order=order,
                replay_preselected=bool(row["replay_preselected"]),
                replay_layout=row["replay_layout"],
                source=row.get("source"),
            )
        )
    if not slots:
        raise SlotMatrixError(f"{unit}: no slots in the matrix")
    verify_slots(slots)
    return slots


def expected_launch_order(slot: Slot) -> tuple[str, ...] | None:
    """The §2.4 rotation for U7 and U8 slots; None for prepared-protocol units."""
    if slot.unit in {"U7r0", "U7r1"}:
        k = slot.slot_index - 1 + slot.repetition
        if set(slot.arms) == {"A", "B", "C"}:
            return C_ROTATIONS[k % 3]
        return ("A", "B") if k % 2 == 0 else ("B", "A")
    if slot.unit in {"U8c", "U8n"}:
        flip = 1 if slot.unit == "U8n" else 0
        return ("A", "B") if (slot.slot_index - 1 + flip) % 2 == 0 else ("B", "A")
    return None


def expected_u8_cell(slot_index: int) -> str:
    """U8 cells rotate per task: (c1m0,c0m1,c1m1) -> (c0m1,c1m1,c1m0) -> (c1m1,c1m0,c0m1)."""
    task = (slot_index - 1) // 3
    rot = task % 3
    cells = U8_CELLS[rot:] + U8_CELLS[:rot]
    return cells[(slot_index - 1) % 3]


def verify_slots(slots: Sequence[Slot]) -> None:
    """Reject any matrix that breaks identity, contiguity or the pre-registered order."""
    if [slot.slot_index for slot in slots] != list(range(1, len(slots) + 1)):
        raise SlotMatrixError("slot indices must be contiguous from 1 in matrix order")
    if len({slot.slot_id for slot in slots}) != len(slots):
        raise SlotMatrixError("slot IDs repeat")
    for slot in slots:
        if slot.slot_id != f"{slot.unit}-s{slot.slot_index:02d}":
            raise SlotMatrixError(f"{slot.slot_id}: slot ID does not match unit and index")
        if (
            not slot.arms
            or len(set(slot.launch_order)) != len(slot.launch_order)
            or sorted(slot.launch_order) != sorted(slot.arms)
            or not set(slot.arms) <= set(ARM_LABELS)
        ):
            raise SlotMatrixError(f"{slot.slot_id}: launch order is not a permutation of its arms")
        expected = expected_launch_order(slot)
        if expected is not None and tuple(slot.launch_order) != expected:
            raise SlotMatrixError(f"{slot.slot_id}: launch order differs from the §2.4 rotation")
        if slot.unit in {"U8c", "U8n"} and slot.cell != expected_u8_cell(slot.slot_index):
            raise SlotMatrixError(f"{slot.slot_id}: U8 cell rotation differs from §2.4")
        if slot.replay_preselected and not slot.replay_layout:
            raise SlotMatrixError(f"{slot.slot_id}: a replay pair needs its fixed layout")


def utc(seconds: float) -> str:
    return datetime.fromtimestamp(seconds, tz=UTC).isoformat()


def parse_utc(value: object) -> float | None:
    """Epoch seconds of an ISO-8601 timestamp with an offset; None when unknown."""
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.timestamp()


def agent_interval(result: Mapping[str, Any] | None) -> tuple[str | None, str | None]:
    """Harbor ``agent_execution`` start/end: the root run begins after setup (and barrier)."""
    timing = (result or {}).get("agent_execution")
    if not isinstance(timing, Mapping):
        return None, None
    start, end = timing.get("started_at"), timing.get("finished_at")
    return (
        start if parse_utc(start) is not None else None,
        end if parse_utc(end) is not None else None,
    )


class LaunchedTrial(Protocol):
    async def wait(self) -> int:
        """Wait for the child to exit; return its exit code."""

    async def stop(self) -> str | None:
        """Terminate, wait the cleanup bound, then kill; return an error class if forced."""


class ArmDriver(Protocol):
    def prepare(self, slot: Slot, arm: str) -> Any:
        """Synchronous per-arm preparation before any launch (secrets, barrier)."""

    async def launch(self, slot: Slot, arm: str, prepared: Any) -> LaunchedTrial:
        """Spawn the arm's child and return at once; no awaiting its work."""

    def release(self, slot: Slot, arm: str, prepared: Any) -> str | None:
        """Undo preparation after the arm exits; return an error class on failure."""


@dataclass(frozen=True)
class StopDecision:
    failure_class: str
    reason: str
    invalidates_slot: bool = False


class SlotGuard(Protocol):
    name: str

    def before_slot(self, slot: Slot) -> StopDecision | None:
        """Refuse the slot before any launch, or None to allow it."""

    def after_slot(self, slot: Slot, report: SlotReport) -> StopDecision | None:
        """Stop the unit after a finished slot, or None to continue."""


@dataclass
class ArmRun:
    arm: str
    position: int
    host_launch_utc: str | None = None
    launched_at: float | None = None
    exited_at: float | None = None
    host_exit_utc: str | None = None
    exit_code: int | None = None
    error: str | None = None


@dataclass
class SlotReport:
    slot: Slot
    runs: dict[str, ArmRun]
    rows: dict[str, dict[str, Any]] = field(default_factory=dict)
    launch_skew_s: float | None = None
    agent_start_skew_s: float | None = None
    pair_sync: bool | None = None
    agent_start_order: tuple[str, ...] = ()
    concurrent: dict[str, int | None] = field(default_factory=dict)
    barrier_used: bool = False
    stop: StopDecision | None = None

    def concurrency_fields(self, arm: str) -> dict[str, Any]:
        """Paired-slot receipt fields under the coordinator's canonical column names.

        Call overlap (``overlapping_calls``) is derived later from ``call_ledger``
        intervals by the data tables, so the runner never writes it.
        """
        run = self.runs[arm]
        row = self.rows.get(arm, {})
        return {
            "slot_id": self.slot.slot_id,
            "position": run.position,
            "agent_start_rank": (
                self.agent_start_order.index(arm) if arm in self.agent_start_order else None
            ),
            "host_launch_utc": run.host_launch_utc,
            "agent_start_utc": row.get("agent_start_utc"),
            "dispatch_skew_s": self.launch_skew_s,
            "agent_start_skew_s": self.agent_start_skew_s,
            "pair_sync": self.pair_sync,
            "barrier_used": self.barrier_used,
            "concurrent_trials": self.concurrent.get(arm),
            **EXTERNAL_USAGE,
        }

    def summary(self) -> dict[str, Any]:
        return {
            "slot_id": self.slot.slot_id,
            "task": self.slot.task,
            "cell": self.slot.cell,
            "repetition": self.slot.repetition,
            "launch_order": list(self.slot.launch_order),
            "agent_start_order": list(self.agent_start_order),
            "host_launch_utc": {arm: run.host_launch_utc for arm, run in self.runs.items()},
            "host_exit_utc": {arm: run.host_exit_utc for arm, run in self.runs.items()},
            "exit_codes": {arm: run.exit_code for arm, run in self.runs.items()},
            "dispatch_errors": {arm: run.error for arm, run in self.runs.items() if run.error},
            "dispatch_skew_s": self.launch_skew_s,
            "agent_start_skew_s": self.agent_start_skew_s,
            "pair_sync": self.pair_sync,
            "barrier_used": self.barrier_used,
            "concurrent_trials": dict(self.concurrent),
            "validity": {arm: row.get("validity") for arm, row in self.rows.items()},
            "stop": None if self.stop is None else self.stop.__dict__,
            **EXTERNAL_USAGE,
        }


@dataclass
class UnitReport:
    slots: list[SlotReport] = field(default_factory=list)
    stop: StopDecision | None = None
    stopped_before: str | None = None

    @property
    def complete(self) -> bool:
        return self.stop is None

    def summary(self) -> dict[str, Any]:
        synced = [report.pair_sync for report in self.slots if len(report.runs) > 1]
        skews = [
            report.agent_start_skew_s
            for report in self.slots
            if report.agent_start_skew_s is not None
        ]
        return {
            "slots_run": len(self.slots),
            "complete": self.complete,
            "stop": None if self.stop is None else self.stop.__dict__,
            "stopped_before": self.stopped_before,
            "pair_sync_false": sum(value is False for value in synced),
            "pair_sync_unknown": sum(value is None for value in synced),
            "max_agent_start_skew_s": max(skews) if skews else None,
            "max_dispatch_skew_s": max(
                (r.launch_skew_s for r in self.slots if r.launch_skew_s is not None),
                default=None,
            ),
        }


Collector = Callable[[Slot, ArmRun], Awaitable[dict[str, Any]]]


class PairedDispatcher:
    """Run slots strictly one after another; arms inside a slot run concurrently."""

    def __init__(
        self,
        *,
        driver: ArmDriver,
        collect: Collector,
        guards: Sequence[SlotGuard] = (),
        on_slot: Callable[[SlotReport], None] | None = None,
        watchdog_s: float = WATCHDOG_S,
        launch_skew_limit_s: float = LAUNCH_SKEW_LIMIT_S,
        agent_sync_limit_s: float = AGENT_SYNC_LIMIT_S,
        barrier_used: bool = False,
        monotonic: Callable[[], float] = time.monotonic,
        wall: Callable[[], float] = time.time,
    ) -> None:
        self.driver = driver
        self.collect = collect
        self.guards = tuple(guards)
        self.on_slot = on_slot
        self.watchdog_s = watchdog_s
        self.launch_skew_limit_s = launch_skew_limit_s
        self.agent_sync_limit_s = agent_sync_limit_s
        self.barrier_used = barrier_used
        self.monotonic = monotonic
        self.wall = wall

    async def run(self, slots: Sequence[Slot]) -> UnitReport:
        unit = UnitReport()
        for slot in slots:
            decision = self._before(slot)
            if decision is not None:
                unit.stop, unit.stopped_before = decision, slot.slot_id
                break
            report = await self.run_slot(slot)
            unit.slots.append(report)
            if self.on_slot is not None:
                self.on_slot(report)
            if report.stop is not None:
                unit.stop = report.stop
                break
        return unit

    def _before(self, slot: Slot) -> StopDecision | None:
        for guard in self.guards:
            decision = guard.before_slot(slot)
            if decision is not None:
                return decision
        return None

    async def run_slot(self, slot: Slot) -> SlotReport:
        prepared: dict[str, Any] = {}
        runs = {arm: ArmRun(arm, position) for position, arm in enumerate(slot.launch_order)}
        report = SlotReport(slot, runs, barrier_used=self.barrier_used)
        try:
            for arm in slot.launch_order:
                prepared[arm] = self.driver.prepare(slot, arm)
        except Exception as error:
            # Nothing was launched; refuse the slot instead of running a partial pair.
            for arm in prepared:
                self.driver.release(slot, arm, prepared[arm])
            report.stop = StopDecision("dispatcher_prepare", type(error).__name__, True)
            for arm, run in runs.items():
                run.error = "prepare_" + type(error).__name__
                report.rows[arm] = {
                    "validity": "invalid",
                    "outcome": "unknown",
                    "failure_class": "dispatcher_prepare",
                }
            for guard in self.guards:
                guard.after_slot(slot, report)  # release reservations; the stop stands
            return report
        supervisors: list[asyncio.Task[None]] = []
        for arm in slot.launch_order:
            run = runs[arm]
            try:
                handle = await self.driver.launch(slot, arm, prepared[arm])
            except Exception as error:
                handle, run.error = None, "launch_" + type(error).__name__
            run.launched_at = self.monotonic()
            run.host_launch_utc = utc(self.wall())
            if handle is not None:
                supervisors.append(asyncio.create_task(self._supervise(run, handle)))
            else:
                run.exited_at, run.host_exit_utc = run.launched_at, run.host_launch_utc
        launched = [run.launched_at for run in runs.values() if run.launched_at is not None]
        if len(runs) > 1 and len(launched) == len(runs):
            report.launch_skew_s = round(max(launched) - min(launched), 6)
        # Every arm finishes (or is stopped by its own watchdog); none is cancelled
        # because a sibling failed.
        if supervisors:
            await asyncio.gather(*supervisors)
        for arm in slot.launch_order:
            released = self.driver.release(slot, arm, prepared[arm])
            if released and runs[arm].error is None:
                runs[arm].error = released
        for arm in slot.launch_order:
            report.rows[arm] = await self.collect(slot, runs[arm])
        self._derive(report)
        report.stop = self._after(slot, report)
        return report

    async def _supervise(self, run: ArmRun, handle: LaunchedTrial) -> None:
        try:
            run.exit_code = await asyncio.wait_for(handle.wait(), timeout=self.watchdog_s)
        except TimeoutError:
            run.error = "watchdog_timeout"
            await self._stop(run, handle)
        except asyncio.CancelledError:
            # The dispatcher itself is being cancelled: stop the child, then propagate.
            run.error = "dispatcher_cancelled"
            await self._stop(run, handle)
            raise
        except Exception as error:
            run.error = "supervise_" + type(error).__name__
            await self._stop(run, handle)
        finally:
            run.exited_at = self.monotonic()
            run.host_exit_utc = utc(self.wall())

    @staticmethod
    async def _stop(run: ArmRun, handle: LaunchedTrial) -> None:
        try:
            forced = await handle.stop()
        except Exception as error:
            forced = "stop_" + type(error).__name__
        if forced:
            run.error = forced

    def _derive(self, report: SlotReport) -> None:
        starts = {arm: parse_utc(row.get("agent_start_utc")) for arm, row in report.rows.items()}
        known = {arm: value for arm, value in starts.items() if value is not None}
        report.agent_start_order = tuple(sorted(known, key=lambda arm: (known[arm], arm)))
        if len(report.runs) > 1 and len(known) == len(report.runs):
            skew = max(known.values()) - min(known.values())
            report.agent_start_skew_s = round(skew, 6)
            report.pair_sync = skew <= self.agent_sync_limit_s
        latest_launch = max(
            (run.launched_at for run in report.runs.values() if run.launched_at is not None),
            default=None,
        )
        for arm in report.runs:
            report.concurrent[arm] = _concurrent(report, arm, latest_launch, starts)

    def _after(self, slot: Slot, report: SlotReport) -> StopDecision | None:
        """Stop rules after a collected slot; every guard still settles its bookkeeping."""
        decision = None
        if report.launch_skew_s is not None and report.launch_skew_s > self.launch_skew_limit_s:
            for row in report.rows.values():
                row["validity"], row["outcome"] = "invalid", "unknown"
                row["failure_class"] = "dispatch_skew_exceeded"
            decision = StopDecision(
                "dispatch_skew_exceeded",
                f"launch skew {report.launch_skew_s:.3f}s exceeds {self.launch_skew_limit_s}s",
                True,
            )
        invalid = [arm for arm, row in report.rows.items() if row.get("validity") != "valid"]
        if invalid and decision is None:
            classes = sorted({str(report.rows[arm].get("failure_class")) for arm in invalid})
            decision = StopDecision(
                "infrastructure_invalid_arm", f"arms {invalid} invalid: {', '.join(classes)}"
            )
        for guard in self.guards:
            guarded = guard.after_slot(slot, report)
            if guarded is not None and decision is None:
                decision = guarded
        return decision


def _concurrent(
    report: SlotReport,
    arm: str,
    latest_launch: float | None,
    starts: Mapping[str, float | None],
) -> int | None:
    """Other trials alive on the host at this trial's agent start.

    Slots never overlap and the execution lock excludes other tracks, so only
    siblings can be active. The reference instant is the agent start when known;
    otherwise the moment the last sibling was launched.
    """
    run = report.runs[arm]
    if run.launched_at is None:
        return None
    reference_wall = starts.get(arm)
    count = 0
    for other, sibling in report.runs.items():
        if other == arm or sibling.launched_at is None:
            continue
        if reference_wall is not None:
            launch = parse_utc(sibling.host_launch_utc)
            end = parse_utc(sibling.host_exit_utc)
            if launch is None or end is None:
                return None
            count += int(launch <= reference_wall <= end)
        elif latest_launch is not None and sibling.exited_at is not None:
            count += int(sibling.launched_at <= latest_launch <= sibling.exited_at)
    return count


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def finite_or_none(value: object) -> float | None:
    if type(value) in (int, float) and math.isfinite(value):  # type: ignore[arg-type]
        return float(value)  # type: ignore[arg-type]
    return None


# --- child processes -----------------------------------------------------------

INHERITED_ENV = frozenset(
    {
        "PATH",
        "HOME",
        "USER",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "TMPDIR",
        "SSL_CERT_FILE",
        "SSL_CERT_DIR",
        "REQUESTS_CA_BUNDLE",
        "HTTPS_PROXY",
        "HTTP_PROXY",
        "NO_PROXY",
        "CODEX_HOME",  # the account guard and every child read the same Codex login
    }
)


class ChildProcess:
    """One arm's child; stop() follows r6: SIGTERM, cleanup bound, then kill."""

    def __init__(self, process: Any, log: Any, cleanup_s: float) -> None:
        self.process, self.log, self.cleanup_s = process, log, cleanup_s

    async def wait(self) -> int:
        try:
            return int(await self.process.wait())
        finally:
            self.log.close()

    async def stop(self) -> str | None:
        if self.process.returncode is not None:
            return None
        self.process.terminate()
        try:
            await asyncio.wait_for(self.process.wait(), timeout=self.cleanup_s)
            return None
        except (TimeoutError, asyncio.CancelledError):
            self.process.kill()
            await self.process.wait()
            return "forced_child_stop_cleanup_unverified"
        finally:
            self.log.close()


class SubprocessDriver:
    """Prepare every arm first (key file, barrier folder), then spawn children back to back.

    Each arm runs ``<python> -B <runner> <mode args> --child <index> [--secret-file F]``
    from the run folder with a filtered environment and ``PYTHONPATH=<pinned source>``.
    """

    def __init__(
        self,
        *,
        cells: Mapping[tuple[str, str], Mapping[str, Any]],
        runner: Path,
        mode_args: Sequence[str],
        directory: Path,
        pythonpath: Path,
        key_file: Callable[[], Path],
        barrier_dir: Callable[[Mapping[str, Any]], Path] | None = None,
        cleanup_s: float = 120.0,
        python: str | None = None,
    ) -> None:
        import sys

        self.cells, self.runner, self.mode_args = cells, runner, list(mode_args)
        self.directory, self.pythonpath, self.key_file = directory, pythonpath, key_file
        self.barrier_dir, self.cleanup_s = barrier_dir, cleanup_s
        self.python = python or sys.executable

    def prepare(self, slot: Slot, arm: str) -> dict[str, Any]:
        cell = self.cells[(slot.slot_id, arm)]
        if cell.get("barrier") and self.barrier_dir is not None:
            self.barrier_dir(cell).mkdir(parents=True, exist_ok=True, mode=0o700)
        return {"cell": cell, "secret": self.key_file() if cell["uses_jev"] else None}

    async def launch(self, slot: Slot, arm: str, prepared: dict[str, Any]) -> ChildProcess:
        import os

        cell, secret = prepared["cell"], prepared["secret"]
        command = [
            self.python,
            "-B",
            str(self.runner),
            *self.mode_args,
            "--child",
            str(cell["index"]),
        ]
        if secret is not None:
            command += ["--secret-file", str(secret)]
        env = {key: value for key, value in os.environ.items() if key in INHERITED_ENV}
        env["PYTHONPATH"] = str(self.pythonpath)
        log = (self.directory / f"child-{cell['index']:03}.log").open("xb")
        try:
            process = await asyncio.create_subprocess_exec(
                *command, env=env, cwd=self.runner.parent, stdout=log, stderr=log
            )
        except BaseException:
            log.close()
            raise
        with (self.directory / "trial-starts.jsonl").open("a", encoding="utf-8") as starts:
            starts.write(
                json.dumps(
                    {
                        "index": cell["index"],
                        "trial_name": cell["trial_name"],
                        "slot_id": slot.slot_id,
                        "launched_at": datetime.now(UTC).isoformat(),
                    }
                )
                + "\n"
            )
        return ChildProcess(process, log, self.cleanup_s)

    def release(self, slot: Slot, arm: str, prepared: dict[str, Any]) -> str | None:
        secret = prepared.get("secret")
        if secret is None:
            return None
        try:
            Path(secret).unlink(missing_ok=True)
        except OSError:
            return "credential_cleanup_failed"
        return None


async def _docker(*args: str) -> int:
    process = await asyncio.create_subprocess_exec(
        "docker", *args, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
    )
    return await process.wait()


async def prebuild_images(
    task_dirs: Sequence[Path], *, docker: Callable[..., Awaitable[int]] = _docker
) -> list[dict[str, Any]]:
    """Pull each agent image and build each verifier image once, before any slot.

    Harbor serializes same-image builds only inside one process, and each arm is its
    own child, so without this the first slot builds a task's verifier image twice
    at once. Images already present are skipped. The verifier tag is Harbor's own
    content name (``hb__<environment_id>``) of the tests directory, so every later
    per-trial build of the same Dockerfile is a cache hit. Docker only; no model.
    """
    from harbor.environments.definition import environment_content_hash
    from harbor.environments.docker.docker import _sanitize_docker_image_name
    from harbor.models.task.task import Task

    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for task_dir in task_dirs:
        task = Task(task_dir)
        agent = str(task.config.environment.docker_image)
        tests = task.paths.tests_dir
        verifier = _sanitize_docker_image_name(
            "hb__" + environment_content_hash(tests, docker_image=None)
        )
        for role, image, action in (
            ("agent", agent, ("pull", agent)),
            ("verifier", verifier, ("build", "--tag", verifier, str(tests))),
        ):
            if image in seen:
                continue
            seen.add(image)
            present = await docker("image", "inspect", image) == 0
            if not present and await docker(*action) != 0:
                raise RuntimeError(f"{role} image for {task.name} could not be prepared")
            records.append(
                {
                    "role": role,
                    "task": task.name,
                    "image": image,
                    "action": "present" if present else action[0],
                }
            )
    return records
