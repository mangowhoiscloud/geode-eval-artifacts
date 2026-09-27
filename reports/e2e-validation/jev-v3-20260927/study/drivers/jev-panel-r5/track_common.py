"""Shared plumbing for the private P (panel, Score-S) and G (generation) track drivers.

Run-folder code, like the E-track runner: the folder is pinned once to a clean
fixed-SHA checkout (``source_pin``) and reuses the E-track host guards
(``run_guards``: one host lock, the G0 account, the quota ledger). Nothing here
prints, logs or records a credential. Every secret is read from GEODE's local
settings only: the Codex login through GEODE's own subscription adapter, the
TypeSafe key from ``[local-path-withheld] (owner-only), never from the process env.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import sys
import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
RUN_ROOT = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import source_pin  # noqa: E402
from run_guards import (  # noqa: E402
    AUTH_MARGIN_SLACK_S,  # noqa: F401 - drivers read tc.AUTH_MARGIN_SLACK_S
    ExecutionLock,
    QuotaLedger,
    ScheduleOverlapError,
    account_fields,
    account_refusal,
    codex_auth_file,
    latest_snapshot,
    live_snapshot,
    read_account_claims,
)

QUOTA_LEDGER = RUN_ROOT / "quota-ledger.csv"
JEV_LEDGER = RUN_ROOT / "jev-cost-ledger.jsonl"
SNAPSHOT_MAX_AGE_S = 3600.0
QUOTA_CHECK_EVERY = 300  # 05 §7: a reading every 300 Astra calls in larger units
EXTERNAL_USAGE = {
    "external_account_usage": "unknown",
    "external_usage_reason": "shared-account-video-session",
}
FREEZE_DIGESTS = (
    "policy_digest",
    "reset_digest",
    "case_sha256",
    "task_checksum",
    "verifier_sha256",
)
ASTRA_ROUTE = "openai/subscription/gpt-6-astra/xhigh"
JEV_ROUTE = "typesafe/payg/jev-1.13.0/none"
BLOCK_SCHEMA = "jev-v3.private-trial-receipt@1"
RESET_BOUNDARY = {
    "session": "one stateless call per planned judgment; no conversation, tool or loop state",
    "files": "no workspace; frozen inputs are read from the run folder only",
    "cache": "no local cache; provider-side prompt caching is not controlled and stays unknown",
}
# Env keys are refused so a stray shell export can never become the route (03 §3).
FORBIDDEN_ENV_KEYS = ("TYPESAFE_API_KEY", "OPENROUTER_API_KEY", "OPENAI_API_KEY")
SECRET_MARKERS = ("access_token", "refresh_token", "id_token", "apikey_", "Bearer ")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_new(path: Path, value: Any) -> str:
    """Exclusive-create a 0600 JSON file; return its sha256."""
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    text = (
        value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    )
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    return hashlib.sha256(text.encode()).hexdigest()


def append_jsonl(path: Path, row: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def now() -> str:
    return datetime.now(UTC).isoformat()


def pinned_source() -> tuple[Path, str]:
    """The run folder's fixed checkout; its modules are importable afterwards."""
    source, revision = source_pin.load_source_pin(ROOT)
    if str(source) not in sys.path:
        sys.path.insert(1, str(source))
    return source, revision


# --- secrets (values never leave these functions) -------------------------------------


def load_typesafe_key(*, home: Path | None = None, environ: Mapping[str, str] | None = None) -> Any:
    """The Jev key from GEODE's local settings file ``[local-path-withheld] (owner-only, 0600)."""
    from dotenv import dotenv_values
    from pydantic import SecretStr

    env = os.environ if environ is None else environ
    if any(env.get(name) for name in FORBIDDEN_ENV_KEYS):
        raise RuntimeError(
            "provider keys in the process environment are refused; use [local-path-withheld]"
        )
    path = (home or Path.home()) / ".geode" / ".env"
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise RuntimeError("GEODE settings file must be a regular owner-only file")
    value = dotenv_values(path, interpolate=False).get("TYPESAFE_API_KEY")
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError("TypeSafe key unavailable in GEODE settings")
    return SecretStr(value.strip())


def astra_adapter() -> Any:
    """GEODE's standard subscription route (Codex file login), gpt-6-astra at xhigh per call."""
    from core.llm.adapters import resolve_for

    adapter = resolve_for("openai", "subscription")
    if (adapter.provider, adapter.source) != ("openai", "subscription"):
        raise RuntimeError("the Astra route must be the openai subscription adapter")
    return adapter


def pin_runtime_settings() -> None:
    """05 §3 route rules for direct judge calls: one attempt per call, global engine llm."""
    from core.config import settings
    from core.config.policy_source import EMPTY_POLICY_SOURCES
    from core.llm.adapters import bootstrap_builtins

    bootstrap_builtins(policy_sources=EMPTY_POLICY_SOURCES)
    if settings.judgment_engine != "llm":
        raise RuntimeError("global Jev judgment must stay disabled; drivers own their engines")
    settings.llm_max_retries = 1


def assert_no_secret(directory: Path, values: Sequence[str]) -> None:
    """Fail if any written file carries a secret value or a credential marker."""
    needles = [value for value in values if value] + list(SECRET_MARKERS)
    for path in sorted(p for p in directory.rglob("*") if p.is_file()):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for needle in needles:
            if needle in text:
                raise RuntimeError(f"secret material found in {path.name}")


# --- frozen cells --------------------------------------------------------------------


def cell_digests(
    policy: Mapping[str, Any], *, case_sha256: str, task_checksum: str, verifier_sha256: str
) -> dict[str, str]:
    """The five freeze digests every cell carries (03 §5.1; same names as E-track cells)."""
    from evals.benchmarks.decision_metrics import policy_digest, reset_digest

    return {
        "policy_digest": policy_digest(dict(policy)),
        "reset_digest": reset_digest(RESET_BOUNDARY),
        "case_sha256": case_sha256,
        "task_checksum": task_checksum,
        "verifier_sha256": verifier_sha256,
    }


def check_spec(
    spec: Mapping[str, Any],
    *,
    prefix: str,
    revision: str,
    driver_sha256: str,
    max_concurrency: int,
) -> list[str]:
    """Frozen run-spec checks shared by every P/G driver; return the ordered workload IDs."""
    execution = spec["reproduction"]["execution"]
    suffix = spec["run_id"].removeprefix(prefix)
    ids = list(execution["ordered_workload_ids"])
    digest = hashlib.sha256(json.dumps(ids, ensure_ascii=False, separators=(",", ":")).encode())
    problems = [
        name
        for name, ok in (
            (
                "run_id",
                spec["run_id"].startswith(prefix)
                and suffix[:8].isdigit()
                and suffix[8:] in {""} | {f"-r{n}" for n in range(1, 10)},
            ),
            ("revision", spec["reproduction"]["geode"]["revision"] == revision),
            ("dirty", spec["reproduction"]["geode"]["dirty"] is False),
            (
                "model",
                spec["reproduction"]["model"]
                == {
                    "provider": "openai",
                    "label": "gpt-6-astra",
                    "route": "subscription",
                    "reasoning": "xhigh",
                },
            ),
            ("concurrency", execution["max_concurrency"] == max_concurrency),
            ("workload_ids_sha256", execution["workload_ids_sha256"] == digest.hexdigest()),
            ("pending", not any("PENDING" in str(value) for value in ids)),
            (
                "budget",
                isinstance(execution["budget"].get("limit"), int)
                and execution["budget"]["limit"] > 0,
            ),
            ("driver", driver_sha256 in spec["reproduction"]["harness"]["source"]),
        )
        if not ok
    ]
    if problems:
        raise ValueError(
            f"{spec['run_id']}: run-spec differs from the frozen driver contract: {problems}"
        )
    return ids


def bound_inputs(paths: Sequence[Path]) -> dict[str, str]:
    for path in paths:
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"frozen input must be a regular file: {path}")
    return {str(path): sha(path) for path in sorted(set(paths))}


def check_bound(bound: Mapping[str, str]) -> None:
    changed = [
        path
        for path, digest in bound.items()
        if not Path(path).is_file() or sha(Path(path)) != digest
    ]
    if changed:
        raise ValueError(f"frozen inputs changed: {[Path(p).name for p in changed]}")


# --- admission and in-unit control -----------------------------------------------------


def stop_unit(directory: Path, failure: str, reason: str, **extra: Any) -> None:
    record = {"failure_class": failure, "reason": reason, "at": now(), **extra}
    write_new(directory / f"unit-stop-{datetime.now(UTC):%Y%m%dT%H%M%S%fZ}.json", record)
    print(json.dumps({"unit_stopped": failure, "reason": reason}))


def docker_busy() -> list[str]:
    """Heavy local work for a solo unit (05 §2.5): running containers. Read-only query."""
    try:
        output = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"], capture_output=True, text=True, timeout=20  # noqa: S607 - the operator's docker CLI on PATH
        )
    except (OSError, subprocess.TimeoutExpired):
        return ["docker-status-unknown"]
    if output.returncode != 0:
        return ["docker-status-unknown"]
    return [line for line in output.stdout.splitlines() if line.strip()]


@dataclass
class Admission:
    """A unit that passed every start rule; ``close`` must run in a ``finally``."""

    directory: Path
    unit: str
    run_id: str
    lock: ExecutionLock
    claims: dict[str, Any]
    quota: QuotaLedger
    start: dict[str, str]
    ledger: Any
    solo: dict[str, Any] | None = None
    notes: dict[str, Any] = field(default_factory=dict)
    quota_live: bool = False

    def close(self, *, astra_calls: int, astra_input_tokens: int, snapshot: Any = None) -> None:
        try:
            if snapshot is None and self.quota_live:
                snapshot = live_snapshot()
            used = self.start.get("used_pct")
            self.quota.end_record(
                unit=self.unit,
                snapshot=snapshot,
                start_used_pct=float(used) if used not in (None, "") else None,
                unit_astra_calls=astra_calls,
                unit_astra_input_tokens=astra_input_tokens,
                account=self.claims,
                checkpoint_id=f"{self.unit}-end",
            )
        finally:
            self.lock.release()


def open_run_jev_ledger(path: Path, *, run_id: str, unit: str) -> Any:
    """Bind native unit and settlement IDs to this run and stage on the host ledger."""
    from evals.benchmarks.jev_cost_ledger import (
        RESERVE_INPUT_TOKENS,
        JevCostLedger,
        _normalize_call,
        _require_id,
    )

    run_id = _require_id(run_id, name="run_id")
    ledger_unit = _require_id(run_id + ":" + _require_id(unit, name="unit"), name="unit_id")
    prefix = ledger_unit + ":"

    def bound_unit(unit_id: str) -> str:
        if _require_id(unit_id, name="unit_id") != run_id:
            raise ValueError("ledger unit must match its bound run_id")
        return ledger_unit

    class RunJevCostLedger(JevCostLedger):
        def admit_unit(
            self, unit_id: str, planned_jev_calls: int, *, p95_input_tokens: int | None = None
        ) -> dict[str, Any]:
            return super().admit_unit(
                bound_unit(unit_id), planned_jev_calls, p95_input_tokens=p95_input_tokens
            )

        def reserve(
            self,
            unit_id: str,
            max_calls: int = 1,
            *,
            input_tokens_per_call: int = RESERVE_INPUT_TOKENS,
        ) -> str:
            return super().reserve(
                bound_unit(unit_id), max_calls, input_tokens_per_call=input_tokens_per_call
            )

        def settle(self, reservation_id: str, calls: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
            rows = [_normalize_call(call) for call in calls]
            for row in rows:
                if row["call_id"] is not None:
                    row["call_id"] = prefix + row["call_id"]
            return super().settle(reservation_id, rows)

    return RunJevCostLedger.open(path)


def admit(
    directory: Path,
    *,
    unit: str,
    run_id: str,
    lock_mode: str,
    planned_astra: int,
    planned_jev: int,
    required_margin_s: int,
    quota_live: bool,
    solo_check: Callable[[], list[str]] | None = None,
) -> Admission | None:
    """Lock, G0 account, quota (90%), Jev ledger admission and STOP; None when refused."""
    from evals.benchmarks.jev_cost_ledger import (
        JevBudgetRefusedError,
        JevLedgerError,
    )

    lock = ExecutionLock(RUN_ROOT, mode=lock_mode, run_id=run_id)
    try:
        lock.acquire()
    except ScheduleOverlapError as error:
        stop_unit(directory, "schedule_overlap", str(error), holder=error.holder)
        return None
    try:
        if (directory / "STOP").exists():
            stop_unit(directory, "operator_stop", "STOP file present")
            return _refused(lock)
        solo = None
        if solo_check is not None:
            busy = solo_check()
            solo = {"heavy_work": busy, **EXTERNAL_USAGE}
            if busy:
                stop_unit(
                    directory, "solo_not_quiet", "other heavy work is running", heavy_work=busy
                )
                return _refused(lock)
        try:
            claims = account_fields(read_account_claims(codex_auth_file()), now=time.time())
        except (OSError, ValueError) as error:
            stop_unit(directory, "account_unreadable", type(error).__name__)
            return _refused(lock)
        refusal = account_refusal(claims, required_margin_s=required_margin_s)
        if refusal:
            stop_unit(directory, refusal, "account guard refused the unit")
            return _refused(lock)
        try:
            quota = QuotaLedger(QUOTA_LEDGER)
        except (OSError, ValueError) as error:
            stop_unit(directory, "quota_ledger_unavailable", type(error).__name__)
            return _refused(lock)
        snapshot = (
            live_snapshot() if quota_live else latest_snapshot(quota, max_age_s=SNAPSHOT_MAX_AGE_S)
        )
        start = quota.start_decision(
            unit=unit,
            planned_astra_calls=planned_astra,
            snapshot=snapshot,
            account=claims,
            checkpoint_id=f"{unit}-start",
        )
        if start["decision"] not in ("start", "calibrating"):
            stop_unit(directory, "quota_" + start["decision"].replace("-", "_"), start["notes"])
            return _refused(lock)
        try:
            ledger = open_run_jev_ledger(JEV_LEDGER, run_id=run_id, unit=unit)
            ledger.admit_unit(run_id, planned_jev)
        except JevBudgetRefusedError as error:
            stop_unit(directory, "jev_budget_refused", error.reason)
            return _refused(lock)
        except (OSError, ValueError, JevLedgerError) as error:
            stop_unit(directory, "jev_ledger_unavailable", type(error).__name__)
            return _refused(lock)
        return Admission(
            directory, unit, run_id, lock, claims, quota, start, ledger, solo, quota_live=quota_live
        )
    except BaseException:
        lock.release()
        raise


def _refused(lock: ExecutionLock) -> None:
    lock.release()


class CallControl:
    """Checked before every planned call: STOP file, host lock, account and in-unit quota.

    Returns a failure class to stop the unit before the call, or None. A quota reading
    runs every ``QUOTA_CHECK_EVERY`` Astra dispatches when a live reader is approved.
    """

    def __init__(
        self,
        admission: Admission,
        *,
        reader: Callable[[], Any] | None,
        account_reader: Callable[[], Any] | None = None,
        every: int = QUOTA_CHECK_EVERY,
    ) -> None:
        self.admission, self.reader, self.every = admission, reader, every
        self.account_reader = account_reader or (lambda: read_account_claims(codex_auth_file()))
        self.astra_calls = 0
        self.stopped: str | None = None

    def before_call(self, engine: str) -> str | None:
        if self.stopped is None:
            self.stopped = self._check(engine)
        return self.stopped

    def _check(self, engine: str) -> str | None:
        admission = self.admission
        if (admission.directory / "STOP").exists():
            return "operator_stop"
        try:
            admission.lock.verify()
        except ScheduleOverlapError:
            return "schedule_overlap"
        try:
            fields = account_fields(self.account_reader(), now=time.time())
        except (OSError, ValueError):
            return "account_unreadable"
        refusal = account_refusal(fields, required_margin_s=600, first=admission.claims)
        if refusal:
            return refusal
        if engine == "llm":
            self.astra_calls += 1
            if self.reader is not None and self.astra_calls % self.every == 0:
                return admission.quota.in_unit_decision(self.reader(), unit=admission.unit)
        return None


def block_receipt(
    admission: Admission,
    *,
    block_id: str,
    lock_mode: str,
    source_revision: str,
    freeze_sha256: str,
    extra: Mapping[str, Any],
) -> Path:
    """One withheld-private receipt per panel, G or solo block (receipt field list)."""
    status: dict[str, Any] = {}
    try:
        status = admission.ledger.status()
    except Exception:  # the receipt still records the unit when the ledger is unreadable
        status = {"error": "ledger_status_unavailable"}
    used = admission.start.get("used_pct")
    receipt = {
        "schema_id": BLOCK_SCHEMA,
        "run_id": admission.run_id,
        "unit": admission.unit,
        "attempt_id": f"{admission.run_id}-block",
        "block_id": block_id,
        "lock_mode": lock_mode,
        "codex_account_fp12": admission.claims.get("codex_account_fp12"),
        "plan_claim": admission.claims.get("plan_claim"),
        "auth_expiry_margin_s": admission.claims.get("auth_expiry_margin_s"),
        "account_matches_g0": admission.claims.get("account_matches_g0"),
        "quota_checkpoint_id": admission.start.get("checkpoint_id"),
        "used_pct_at_unit_start": float(used) if used not in (None, "") else None,
        "reset_at_kst": admission.start.get("reset_at_kst") or None,
        **EXTERNAL_USAGE,
        "solo": admission.solo,
        "jev_ledger_status": status,
        "source_revision": source_revision,
        "freeze_sha256": freeze_sha256,
        **extra,
    }
    folder = admission.directory / "private-receipts"
    folder.mkdir(mode=0o700, exist_ok=True)
    path = folder / f"{admission.run_id}-block.json"
    write_new(path, receipt)
    return path
