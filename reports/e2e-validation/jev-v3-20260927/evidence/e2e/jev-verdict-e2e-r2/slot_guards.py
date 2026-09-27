"""Slot guards for the paired dispatcher (05 v2 §1.2, §2.5, §4.3, §7, §9).

Each guard may refuse a slot before any arm launches, or stop the unit after a
finished slot. Stdlib only; the Jev ledger comes from the pinned GEODE source.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from paired_dispatch import Slot, SlotReport, StopDecision
from run_guards import (
    AUTH_MARGIN_SLACK_S,
    AccountClaims,
    ExecutionLock,
    QuotaLedger,
    QuotaSnapshot,
    ScheduleOverlapError,
    account_fields,
    account_refusal,
)


class LockGuard:
    """The unit must still own the host execution lock around every slot."""

    name = "execution_lock"

    def __init__(self, lock: ExecutionLock) -> None:
        self.lock = lock

    def _check(self) -> StopDecision | None:
        try:
            self.lock.verify()
        except ScheduleOverlapError as error:
            return StopDecision("schedule_overlap", str(error))
        return None

    def before_slot(self, slot: Slot) -> StopDecision | None:
        return self._check()

    def after_slot(self, slot: Slot, report: SlotReport) -> StopDecision | None:
        return self._check()


class StopFileGuard:
    """A coordinator or user stop: ``<phase>/STOP`` refuses the next slot."""

    name = "operator_stop"

    def __init__(self, directory: Path) -> None:
        self.path = directory / "STOP"

    def before_slot(self, slot: Slot) -> StopDecision | None:
        return StopDecision("operator_stop", "STOP file present") if self.path.exists() else None

    def after_slot(self, slot: Slot, report: SlotReport) -> StopDecision | None:
        return None


class AccountGuard:
    """Fingerprint, plan and expiry margin before every slot; values feed receipts."""

    name = "account"

    def __init__(
        self,
        first: Mapping[str, Any],
        slots: Sequence[Slot],
        *,
        reader: Callable[[], AccountClaims],
        slot_bound_s: float,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.first = dict(first)
        self.remaining = {slot.slot_id: len(slots) - i for i, slot in enumerate(slots)}
        self.reader, self.slot_bound_s, self.clock = reader, slot_bound_s, clock
        self.fields: dict[str, dict[str, Any]] = {}

    def before_slot(self, slot: Slot) -> StopDecision | None:
        try:
            fields = account_fields(self.reader(), now=self.clock())
        except (OSError, ValueError):
            return StopDecision("account_unreadable", "Codex auth file unreadable")
        self.fields[slot.slot_id] = fields
        required = int(self.remaining[slot.slot_id] * self.slot_bound_s + AUTH_MARGIN_SLACK_S)
        refusal = account_refusal(fields, required_margin_s=required, first=self.first)
        return None if refusal is None else StopDecision(refusal, f"account guard: {refusal}")

    def after_slot(self, slot: Slot, report: SlotReport) -> StopDecision | None:
        return None


class QuotaGuard:
    """One mid-unit reading for units planned above 300 Astra calls (05 v2 §7)."""

    name = "quota"

    def __init__(
        self,
        ledger: QuotaLedger,
        unit: str,
        slots: Sequence[Slot],
        planned: int,
        reader: Callable[[], QuotaSnapshot | None] | None,
    ) -> None:
        self.ledger, self.unit, self.reader = ledger, unit, reader
        self.check_at = (
            slots[len(slots) // 2].slot_id if planned > 300 and reader is not None else None
        )

    def before_slot(self, slot: Slot) -> StopDecision | None:
        if slot.slot_id != self.check_at or self.reader is None:
            return None
        refusal = self.ledger.in_unit_decision(self.reader(), unit=self.unit)
        return None if refusal is None else StopDecision(refusal, "in-unit quota at or above 95%")

    def after_slot(self, slot: Slot, report: SlotReport) -> StopDecision | None:
        return None


class JevGuard:
    """Reserve each Jev arm before launch; settle its observed calls after collection."""

    name = "jev_ledger"

    def __init__(
        self,
        ledger: Any,
        run_id: str,
        cells: Mapping[tuple[str, str], Mapping[str, Any]],
        *,
        calls_per_trial: int | None = None,
    ) -> None:
        self.ledger, self.run_id, self.cells = ledger, run_id, cells
        self.calls_per_trial = calls_per_trial  # used only for cells without a frozen cap
        self.reservations: dict[tuple[str, str], str] = {}
        self.settlements: dict[tuple[str, str], dict[str, Any]] = {}

    def before_slot(self, slot: Slot) -> StopDecision | None:
        from evals.benchmarks.jev_cost_ledger import JevBudgetError, JevLedgerError

        for arm in slot.launch_order:
            cell = self.cells[(slot.slot_id, arm)]
            if not cell["uses_jev"]:
                continue
            cap = int(cell.get("jev_call_cap") or self.calls_per_trial or 0)
            if cap < 1:
                return StopDecision(
                    "jev_call_cap_missing", f"{cell.get('trial_name')}: no frozen cap"
                )
            try:
                self.reservations[(slot.slot_id, arm)] = self.ledger.reserve(self.run_id, cap)
            except JevBudgetError as error:
                for key in [k for k in self.reservations if k[0] == slot.slot_id]:
                    self.ledger.settle(self.reservations.pop(key), [])
                return StopDecision("jev_budget_refused", error.reason)
            except (JevLedgerError, ValueError) as error:
                # An unreadable ledger: open reservations stay counted as committed.
                return StopDecision("jev_ledger_error", type(error).__name__)
        return None

    def after_slot(self, slot: Slot, report: SlotReport) -> StopDecision | None:
        from evals.benchmarks.jev_cost_ledger import JevBudgetExhaustedError, JevLedgerError

        decision = None
        for arm in slot.launch_order:
            key = (slot.slot_id, arm)
            if key not in self.reservations:
                continue
            run = report.runs[arm]
            calls = [] if run.launched_at is None else report.rows.get(arm, {}).get("jev_calls", [])
            try:
                self.settlements[key] = self.ledger.settle(self.reservations.pop(key), calls)
            except JevBudgetExhaustedError as error:
                self.settlements[key] = dict(error.record or {})
                decision = decision or StopDecision("jev_budget_exhausted", error.reason)
            except (JevLedgerError, ValueError) as error:
                # The reservation stays open, so the ledger keeps counting it as committed.
                decision = decision or StopDecision("jev_ledger_error", type(error).__name__)
        return decision


class PreflightGuard:
    """Re-verify the frozen inputs before every slot, as the serial r6 dispatch did per cell."""

    name = "preflight"

    def __init__(self, check: Callable[[], Any]) -> None:
        self.check = check

    def before_slot(self, slot: Slot) -> StopDecision | None:
        try:
            self.check()
        except Exception as error:  # any drift refuses the slot; nothing launched
            return StopDecision("frozen_input_changed", type(error).__name__)
        return None

    def after_slot(self, slot: Slot, report: SlotReport) -> StopDecision | None:
        return None


PRIVATE_RECEIPT_SCHEMA = "jev-v3.private-trial-receipt@1"
FREEZE_DIGESTS = (
    "policy_digest",
    "reset_digest",
    "case_sha256",
    "task_checksum",
    "verifier_sha256",
)


def private_receipt(
    report: SlotReport,
    arm: str,
    *,
    cell: Mapping[str, Any],
    attempt: Mapping[str, Any],
    context: Mapping[str, Any],
    account: AccountGuard,
    jev: JevGuard,
    quota_start: Mapping[str, str],
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """One trial's withheld-private receipt; every track runner writes the same columns.

    ``context`` carries run constants: run_id, unit, source_revision, harbor_version,
    image_digest, infra_proof_sha256 and host_environment_sha256.
    """
    settlement = jev.settlements.get((report.slot.slot_id, arm)) or {}
    fields = account.fields.get(report.slot.slot_id) or {}
    used = quota_start.get("used_pct")
    try:
        used_pct = float(used) if used not in (None, "") else None
    except (TypeError, ValueError):
        used_pct = None
    return {
        "schema_id": PRIVATE_RECEIPT_SCHEMA,
        "run_id": context["run_id"],
        "unit": context["unit"],
        "attempt_id": attempt["attempt_id"],
        "trial_name": cell["trial_name"],
        "arm_label": cell["verification_engine"],
        "replay_preselected": cell.get("replay_preselected", False),
        "replay_side": cell.get("replay_side"),
        "codex_account_fp12": fields.get("codex_account_fp12"),
        "plan_claim": fields.get("plan_claim"),
        "auth_expiry_margin_s": fields.get("auth_expiry_margin_s"),
        "account_matches_g0": fields.get("account_matches_g0"),
        "quota_checkpoint_id": quota_start.get("checkpoint_id"),
        "used_pct_at_unit_start": used_pct,
        "reset_at_kst": quota_start.get("reset_at_kst") or None,
        **report.concurrency_fields(arm),
        "in_flight_panel_calls": None,
        "jev_call_cap": cell.get("jev_call_cap"),
        "jev_reservation_id": settlement.get("reservation_id"),
        "jev_calls_settled": len(settlement.get("calls", [])) if settlement else None,
        "jev_estimate_usd": settlement.get("estimate_usd"),
        "jev_reserve_usd": settlement.get("reserve_usd"),
        "source_revision": context["source_revision"],
        "harbor_version": context["harbor_version"],
        "image_digest": context["image_digest"],
        "infra_proof_sha256": context["infra_proof_sha256"],
        "host_environment_sha256": context["host_environment_sha256"],
        **{name: cell.get(name) for name in FREEZE_DIGESTS},
        "validity": attempt["validity"],
        "outcome": attempt["outcome"],
        "failure_class": attempt["failure_class"],
        "stop_reason": None if report.stop is None else report.stop.failure_class,
        **(extra or {}),
    }


def write_private_receipt(directory: Path, receipt: Mapping[str, Any]) -> Path:
    """Exclusive-create ``<phase>/private-receipts/<attempt_id>.json`` with mode 0600."""
    import json
    import os

    folder = directory / "private-receipts"
    folder.mkdir(mode=0o700, exist_ok=True)
    path = folder / f"{receipt['attempt_id']}.json"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    return path
