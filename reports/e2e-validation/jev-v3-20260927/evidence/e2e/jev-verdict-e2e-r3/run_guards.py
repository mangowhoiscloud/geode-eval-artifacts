"""Host guards shared by every Jev v3 track runner (05 v2 §1.2, §2.5, §7).

Stdlib only; nothing here reads a token into a receipt, prints a credential or
calls a model.

* ``ExecutionLock``: one host lock file ``<run-root>/.execution-lock`` so only one
  track (E ``e2e-slot``, P ``panel-unit``, G ``gen``, solo ``latency-solo``) runs
  at a time. ``fcntl.flock`` is released by the OS when a holder dies, so there is
  no stale lock. A unit that cannot take the lock, or loses it, raises
  ``ScheduleOverlapError`` (``failure_class=schedule_overlap``).
* ``read_account_claims``: the Codex account fingerprint (first 12 hex of
  ``sha256(tokens.account_id)``), the plan claim and the access-token expiry.
  Only these derived values leave the function.
* ``QuotaLedger``: the append-only ``quota-ledger.csv`` (run-packets template
  columns), the cumulative calibration r, the 90 % start rule and the 95 %
  in-unit stop rule. A live snapshot calls GEODE's ``fetch_codex_usage`` only when
  the operator passes the user-approved live flag.
"""

from __future__ import annotations

import base64
import csv
import fcntl
import hashlib
import io
import json
import math
import os
import socket
import time
import urllib.error
import urllib.request
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

LOCK_NAME = ".execution-lock"
LOCK_LOG = ".execution-lock.log.jsonl"
LOCK_SCHEMA = "jev-v3.execution-lock@1"
LOCK_MODES = ("e2e-slot", "panel-unit", "gen", "latency-solo")
EXPECTED_ACCOUNT_FP12 = "anonymous-account-03"
EXPECTED_PLAN = "pro"
AUTH_MARGIN_SLACK_S = 3600
QUOTA_START_LIMIT_PCT = 90.0
QUOTA_STOP_LIMIT_PCT = 95.0
QUOTA_COLUMNS = (
    "checkpoint_id",
    "time_kst",
    "event",
    "used_pct",
    "window_seconds",
    "reset_at_kst",
    "account_fp12",
    "plan",
    "account_matches_g0",
    "program_astra_calls_cum",
    "program_astra_input_tokens_cum",
    "delta_used_pct",
    "delta_astra_calls",
    "r_used_pct_per_100_calls",
    "r_status",
    "next_unit",
    "unit_astra_calls_planned",
    "projected_end_pct",
    "decision",
    "notes",
)
KST = timezone(timedelta(hours=9))


def _iso(seconds: float) -> str:
    return datetime.fromtimestamp(seconds, tz=UTC).isoformat()


def _kst(seconds: float) -> str:
    return datetime.fromtimestamp(seconds, tz=KST).strftime("%Y-%m-%d %H:%M")


class ScheduleOverlapError(RuntimeError):
    """Another track holds, or took over, the host execution lock."""

    failure_class = "schedule_overlap"

    def __init__(self, message: str, holder: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.holder = dict(holder or {})


class ExecutionLock:
    """Exclusive host-wide track lock held for a whole unit.

    E units hold it until their last slot is collected; P and G units hold it to
    their end. The lock file names the holder; ``.execution-lock.log.jsonl`` keeps
    acquire, release and refused events (track switch times for the run-log).
    """

    def __init__(
        self,
        run_root: Path,
        *,
        mode: str,
        run_id: str,
        clock: Callable[[], float] = time.time,
    ) -> None:
        if mode not in LOCK_MODES:
            raise ValueError(f"unknown track mode {mode!r}")
        if not run_id or any(ch in run_id for ch in "\n\r\t/"):
            raise ValueError("run_id must be a single safe token")
        self.path = Path(run_root) / LOCK_NAME
        self.log_path = Path(run_root) / LOCK_LOG
        self.mode, self.run_id, self.clock = mode, run_id, clock
        self._fd: int | None = None
        self._holder: dict[str, Any] | None = None
        self._inode: int | None = None

    @property
    def holder(self) -> dict[str, Any] | None:
        return None if self._holder is None else dict(self._holder)

    def _log(self, event: str, **fields: Any) -> None:
        record = {
            "event": event,
            "at": _iso(self.clock()),
            "mode": self.mode,
            "run_id": self.run_id,
        }
        record.update(fields)
        descriptor = os.open(
            self.log_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_CLOEXEC, 0o600
        )
        with os.fdopen(descriptor, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    def _read_holder(self) -> dict[str, Any]:
        try:
            value = json.loads(self.path.read_text(encoding="utf-8") or "{}")
        except (OSError, ValueError):
            return {}
        return value if isinstance(value, dict) else {}

    def acquire(self) -> dict[str, Any]:
        if self._fd is not None:
            raise RuntimeError("lock already held by this object")
        fd = os.open(self.path, os.O_RDWR | os.O_CREAT | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            os.close(fd)
            holder = self._read_holder()
            self._log("refused", holder=holder)
            raise ScheduleOverlapError(
                f"track lock held by {holder.get('mode')}:{holder.get('run_id')}", holder
            ) from None
        holder = {
            "schema": LOCK_SCHEMA,
            "mode": self.mode,
            "run_id": self.run_id,
            "started_at": _iso(self.clock()),
            "pid": os.getpid(),
            "host": socket.gethostname(),
            "token": uuid.uuid4().hex,
        }
        os.ftruncate(fd, 0)
        os.pwrite(fd, (json.dumps(holder, sort_keys=True) + "\n").encode(), 0)
        os.fsync(fd)
        self._fd, self._holder, self._inode = fd, holder, os.fstat(fd).st_ino
        self._log("acquire", token=holder["token"])
        return dict(holder)

    def verify(self) -> None:
        """Raise ``ScheduleOverlapError`` unless this object still owns the lock file."""
        if self._fd is None or self._holder is None:
            raise ScheduleOverlapError("track lock is not held")
        try:
            inode = os.stat(self.path).st_ino
        except FileNotFoundError:
            inode = None
        current = self._read_holder()
        if inode != self._inode or current.get("token") != self._holder["token"]:
            self._log("lost", current=current)
            raise ScheduleOverlapError("track lock file was replaced or rewritten", current)

    def release(self) -> None:
        if self._fd is None:
            return
        try:
            self._log("release", token=(self._holder or {}).get("token"))
            fcntl.flock(self._fd, fcntl.LOCK_UN)
        finally:
            os.close(self._fd)
            self._fd, self._holder, self._inode = None, None, None

    def __enter__(self) -> ExecutionLock:
        self.acquire()
        return self

    def __exit__(self, *exc: object) -> None:
        self.release()


# --- account -----------------------------------------------------------------


@dataclass(frozen=True)
class AccountClaims:
    """Derived, non-secret account evidence; never a token or a raw account ID."""

    fp12: str | None
    plan: str | None
    expires_at: float | None


def codex_auth_file(environ: Mapping[str, str] | None = None) -> Path:
    """Same resolution as GEODE's ``codex_auth_path``: ``$CODEX_HOME`` or ``~/.codex``."""
    env = os.environ if environ is None else environ
    configured = env.get("CODEX_HOME", "").strip()
    root = Path(configured).expanduser().resolve() if configured else Path.home() / ".codex"
    return root / "auth.json"


def _jwt_claims(token: object) -> dict[str, Any]:
    if not isinstance(token, str):
        return {}
    parts = token.split(".")
    if len(parts) < 2:
        return {}
    try:
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=" * (-len(parts[1]) % 4)))
    except (ValueError, UnicodeDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def read_account_claims(path: Path) -> AccountClaims:
    """Read the file-stored Codex login and keep only fingerprint, plan and expiry."""
    data = json.loads(path.read_text(encoding="utf-8"))
    tokens = data.get("tokens") if isinstance(data, dict) else None
    tokens = tokens if isinstance(tokens, dict) else {}
    account_id = tokens.get("account_id")
    fp12 = (
        hashlib.sha256(account_id.encode()).hexdigest()[:12]
        if isinstance(account_id, str) and account_id
        else None
    )
    plan = None
    expires = None
    for name in ("access_token", "id_token"):
        claims = _jwt_claims(tokens.get(name))
        auth = claims.get("https://api.openai.com/auth")
        if plan is None and isinstance(auth, dict):
            value = auth.get("chatgpt_plan_type")
            plan = value if isinstance(value, str) and value else None
        exp = claims.get("exp")
        if name == "access_token" and type(exp) in (int, float) and math.isfinite(exp) and exp > 0:
            expires = float(exp)
    return AccountClaims(fp12, plan, expires)


def account_fields(
    claims: AccountClaims,
    *,
    now: float,
    expected_fp12: str = EXPECTED_ACCOUNT_FP12,
    expected_plan: str = EXPECTED_PLAN,
) -> dict[str, Any]:
    margin = None if claims.expires_at is None else int(claims.expires_at - now)
    return {
        "codex_account_fp12": claims.fp12,
        "plan_claim": claims.plan,
        "auth_expiry_margin_s": margin,
        "account_matches_g0": claims.fp12 == expected_fp12 and claims.plan == expected_plan,
    }


def account_refusal(
    fields: Mapping[str, Any], *, required_margin_s: int, first: Mapping[str, Any] | None = None
) -> str | None:
    """Failure class that forbids a start, or None (05 v2 §1.2; receipt rules)."""
    if not fields["codex_account_fp12"] or not fields["plan_claim"]:
        return "account_unreadable"
    if not fields["account_matches_g0"]:
        return "account_changed"
    if first is not None and (
        fields["codex_account_fp12"] != first["codex_account_fp12"]
        or fields["plan_claim"] != first["plan_claim"]
    ):
        return "account_changed"
    margin = fields["auth_expiry_margin_s"]
    if margin is None or margin < required_margin_s:
        return "auth_expiry_margin"
    return None


# --- quota -------------------------------------------------------------------


@dataclass(frozen=True)
class QuotaSnapshot:
    """One usage reading; ``used_pct`` is the highest used share over present windows."""

    used_pct: float
    window_seconds: int | None
    reset_at_kst: str | None
    source: str
    windows: tuple[dict[str, Any], ...] = ()


def snapshot_from_usage(usage: Any) -> QuotaSnapshot | None:
    """Convert GEODE ``CodexUsage`` without trusting its window labels.

    GEODE maps WHAM ``primary_window`` to ``five_hour`` and ``secondary_window`` to
    ``weekly`` by position, while G0 showed a single weekly primary window. Every
    present window is therefore projected and the highest share governs.
    """
    if usage is None:
        return None
    windows = []
    for name in ("five_hour", "weekly"):
        window = getattr(usage, name, None)
        utilization = getattr(window, "utilization", None)
        if type(utilization) in (int, float) and math.isfinite(utilization):
            windows.append(
                {
                    "slot": name,
                    "label": getattr(window, "label", None),
                    "used_pct": round(float(utilization) * 100, 3),
                    "resets_at": getattr(window, "resets_at", None),
                }
            )
    if not windows:
        return None
    top = max(windows, key=lambda row: row["used_pct"])
    reset = top["resets_at"]
    try:
        reset_kst = (
            datetime.fromisoformat(reset.replace("Z", "+00:00"))
            .astimezone(KST)
            .strftime("%Y-%m-%d %H:%M")
            if isinstance(reset, str)
            else None
        )
    except ValueError:
        reset_kst = None
    return QuotaSnapshot(top["used_pct"], None, reset_kst, "wham-live", tuple(windows))


def snapshot_from_wham(payload: Any) -> QuotaSnapshot | None:
    """Read WHAM used_percent as percentage points, including the value 1."""
    if not isinstance(payload, dict) or not isinstance(payload.get("rate_limit"), dict):
        return None
    windows = []
    for name in ("primary_window", "secondary_window"):
        body = payload["rate_limit"].get(name)
        if body is None:
            continue
        if not isinstance(body, dict):
            return None
        used = body.get("used_percent")
        if type(used) not in (int, float) or not math.isfinite(used) or not 0 <= used <= 100:
            return None
        seconds = body.get("limit_window_seconds")
        if seconds is not None and (type(seconds) is not int or seconds <= 0):
            return None
        reset = body.get("reset_at")
        reset_kst = None
        try:
            if type(reset) in (int, float) and math.isfinite(reset):
                reset_kst = datetime.fromtimestamp(reset, KST).strftime("%Y-%m-%d %H:%M")
            elif isinstance(reset, str):
                parsed = datetime.fromisoformat(reset.replace("Z", "+00:00"))
                if parsed.tzinfo is not None:
                    reset_kst = parsed.astimezone(KST).strftime("%Y-%m-%d %H:%M")
        except (OverflowError, ValueError, OSError):
            pass
        windows.append(
            {
                "slot": name,
                "used_pct": float(used),
                "window_seconds": seconds,
                "reset_at_kst": reset_kst,
            }
        )
    if not windows:
        return None
    top = max(windows, key=lambda row: row["used_pct"])
    return QuotaSnapshot(
        top["used_pct"], top["window_seconds"], top["reset_at_kst"], "wham-live", tuple(windows)
    )


def live_snapshot() -> QuotaSnapshot | None:
    """One approved WHAM GET; reuse credentials/endpoint but avoid legacy unit inference."""
    from core.llm.codex_oauth_usage import CODEX_WHAM_USAGE_URL, read_codex_oauth_credentials

    credentials = read_codex_oauth_credentials()
    if credentials is None:
        return None
    headers = {"Authorization": f"Bearer {credentials.token}", "Accept": "application/json"}
    if credentials.account_id:
        headers["ChatGPT-Account-Id"] = credentials.account_id
    request = urllib.request.Request(CODEX_WHAM_USAGE_URL, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=8.0) as response:
            if response.status != 200:
                return None
            payload = json.loads(response.read())
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return None
    return snapshot_from_wham(payload)


class QuotaLedger:
    """Append-only quota ledger in the run-packets template layout (05 v2 §7)."""

    def __init__(
        self,
        path: Path,
        *,
        start_limit_pct: float = QUOTA_START_LIMIT_PCT,
        stop_limit_pct: float = QUOTA_STOP_LIMIT_PCT,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.path = Path(path)
        self.start_limit_pct, self.stop_limit_pct, self.clock = (
            start_limit_pct,
            stop_limit_pct,
            clock,
        )
        if not self.path.is_file() or self.path.is_symlink():
            raise FileNotFoundError(
                f"{self.path}: copy run-packets/quota/projection-template.csv here first"
            )
        header = next(csv.reader(io.StringIO(self.path.read_text(encoding="utf-8"))), None)
        if tuple(header or ()) != QUOTA_COLUMNS:
            raise ValueError(f"{self.path}: quota ledger columns differ from the template")

    def rows(self) -> list[dict[str, str]]:
        with self.path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def append(self, **values: Any) -> dict[str, str]:
        unknown = set(values) - set(QUOTA_COLUMNS)
        if unknown:
            raise ValueError(f"unknown quota ledger fields: {sorted(unknown)}")
        row = {
            column: "" if values.get(column) is None else str(values[column])
            for column in QUOTA_COLUMNS
        }
        buffer = io.StringIO()
        csv.writer(buffer, lineterminator="\n").writerow([row[c] for c in QUOTA_COLUMNS])
        descriptor = os.open(self.path, os.O_WRONLY | os.O_APPEND | os.O_CLOEXEC)
        with os.fdopen(descriptor, "a", encoding="utf-8") as handle:
            handle.write(buffer.getvalue())
            handle.flush()
            os.fsync(handle.fileno())
        return row

    def calibration(self) -> tuple[float | None, str]:
        """Fit r on the current G0 account and plan; retain all program totals separately."""
        delta = calls = 0.0
        for row in self.rows():
            if (
                row["event"] != "unit_end"
                or row["account_fp12"] != EXPECTED_ACCOUNT_FP12
                or row["plan"] != EXPECTED_PLAN
            ):
                continue
            try:
                d, c = float(row["delta_used_pct"]), float(row["delta_astra_calls"])
            except ValueError:
                continue
            if math.isfinite(d) and math.isfinite(c) and c > 0:
                delta, calls = delta + max(d, 0.0), calls + c
        if calls <= 0:
            return None, "none"
        if delta < 2:
            return (delta + 1) / (calls / 100), "provisional"
        return delta / (calls / 100), "measured"

    def program_astra_calls(self) -> tuple[int, int]:
        total_calls = total_tokens = 0
        for row in self.rows():
            if row["event"] == "unit_end":
                try:
                    total_calls = max(total_calls, int(row["program_astra_calls_cum"]))
                    total_tokens = max(total_tokens, int(row["program_astra_input_tokens_cum"]))
                except ValueError:
                    continue
        return total_calls, total_tokens

    def start_decision(
        self,
        *,
        unit: str,
        planned_astra_calls: int,
        snapshot: QuotaSnapshot | None,
        account: Mapping[str, Any],
        checkpoint_id: str,
    ) -> dict[str, str]:
        """Record and return the pre-unit decision: start, calibrating or pause-reset."""
        r, status = self.calibration()
        if snapshot is None:
            decision, projected, note = "no-snapshot", None, "record a quota snapshot first"
        else:
            projected = snapshot.used_pct + (r or 0.0) * planned_astra_calls / 100
            if projected > self.start_limit_pct or snapshot.used_pct >= self.stop_limit_pct:
                decision, note = "pause-reset", "projected end over 90%; request a reset"
            elif r is None:
                decision, note = "calibrating", "r unknown before U0 ends; projection = used now"
            else:
                decision, note = "start", ""
        calls, tokens = self.program_astra_calls()
        return self.append(
            checkpoint_id=checkpoint_id,
            time_kst=_kst(self.clock()),
            event="unit_start",
            used_pct=None if snapshot is None else snapshot.used_pct,
            window_seconds=None if snapshot is None else snapshot.window_seconds,
            reset_at_kst=None if snapshot is None else snapshot.reset_at_kst,
            account_fp12=account.get("codex_account_fp12"),
            plan=account.get("plan_claim"),
            account_matches_g0=str(bool(account.get("account_matches_g0"))).lower(),
            program_astra_calls_cum=calls,
            program_astra_input_tokens_cum=tokens,
            r_used_pct_per_100_calls=None if r is None else round(r, 6),
            r_status=status,
            next_unit=unit,
            unit_astra_calls_planned=planned_astra_calls,
            projected_end_pct=None if projected is None else round(projected, 3),
            decision=decision,
            notes=note if snapshot is None else f"{note}; source={snapshot.source}".strip("; "),
        )

    def in_unit_decision(self, snapshot: QuotaSnapshot | None, *, unit: str) -> str | None:
        """Failure class when a mid-unit reading reaches the stop limit, else None."""
        if snapshot is None:
            return None
        self.append(
            checkpoint_id=f"{unit}-mid",
            time_kst=_kst(self.clock()),
            event="unit_mid",
            used_pct=snapshot.used_pct,
            reset_at_kst=snapshot.reset_at_kst,
            next_unit=unit,
            decision="stop" if snapshot.used_pct >= self.stop_limit_pct else "continue",
            notes=f"source={snapshot.source}",
        )
        return "quota_stop" if snapshot.used_pct >= self.stop_limit_pct else None

    def end_record(
        self,
        *,
        unit: str,
        snapshot: QuotaSnapshot | None,
        start_used_pct: float | None,
        unit_astra_calls: int,
        unit_astra_input_tokens: int,
        account: Mapping[str, Any],
        checkpoint_id: str,
    ) -> dict[str, str]:
        """Close a unit; Δ joins calibration only with both readings and observed calls."""
        calls, tokens = self.program_astra_calls()
        delta = (
            None
            if snapshot is None or start_used_pct is None
            else round(snapshot.used_pct - start_used_pct, 3)
        )
        return self.append(
            checkpoint_id=checkpoint_id,
            time_kst=_kst(self.clock()),
            event="unit_end",
            used_pct=None if snapshot is None else snapshot.used_pct,
            reset_at_kst=None if snapshot is None else snapshot.reset_at_kst,
            account_fp12=account.get("codex_account_fp12"),
            plan=account.get("plan_claim"),
            account_matches_g0=str(bool(account.get("account_matches_g0"))).lower(),
            program_astra_calls_cum=calls + unit_astra_calls,
            program_astra_input_tokens_cum=tokens + unit_astra_input_tokens,
            delta_used_pct=delta,
            delta_astra_calls=unit_astra_calls if delta is not None else None,
            next_unit=unit,
            decision="closed",
            notes="external shared-account usage is included in delta (not subtracted)",
        )


def latest_snapshot(ledger: QuotaLedger, *, max_age_s: float) -> QuotaSnapshot | None:
    """The newest operator snapshot row (event ``snapshot``) if recent enough."""
    for row in reversed(ledger.rows()):
        if row["event"] != "snapshot":
            continue
        try:
            recorded = datetime.strptime(row["time_kst"], "%Y-%m-%d %H:%M").replace(tzinfo=KST)
            used = float(row["used_pct"])
        except ValueError:
            return None
        if ledger.clock() - recorded.timestamp() > max_age_s or not math.isfinite(used):
            return None
        window = int(row["window_seconds"]) if row["window_seconds"].isdigit() else None
        return QuotaSnapshot(used, window, row["reset_at_kst"] or None, "operator-snapshot")
    return None


def record_snapshot(
    ledger: QuotaLedger,
    snapshot: QuotaSnapshot,
    *,
    account: Mapping[str, Any],
    checkpoint_id: str,
    notes: Sequence[str] = (),
) -> dict[str, str]:
    return ledger.append(
        checkpoint_id=checkpoint_id,
        time_kst=_kst(ledger.clock()),
        event="snapshot",
        used_pct=snapshot.used_pct,
        window_seconds=snapshot.window_seconds,
        reset_at_kst=snapshot.reset_at_kst,
        account_fp12=account.get("codex_account_fp12"),
        plan=account.get("plan_claim"),
        account_matches_g0=str(bool(account.get("account_matches_g0"))).lower(),
        notes="; ".join([f"source={snapshot.source}", *notes]),
    )


# --- Jev dispatch caps --------------------------------------------------------


def _single(values: list[Any], what: str) -> Any:
    if len(values) != 1:
        raise ValueError(f"cannot derive the Jev call cap: {what} found {len(values)} times")
    return values[0]


def derive_jev_call_caps(source: Path) -> dict[str, Any]:
    """Per-trial Jev dispatch caps read from the pinned runtime source; fail closed on drift.

    Judge (verdict E2E arms B and C): every final answer gets one ``turn_verification``
    call and a failed verdict continues at most ``_verify_continuation_budget`` times,
    so a trial has ``1 + budget`` judgments. Each judgment is one logical call whose
    fail-fast wrapper dispatches at most ``max(empty-output attempts, 2)`` times (a
    connection error retries once); ``settings.llm_max_retries = 1`` adds no loop
    retry, and the Jev HTTP client (default transport) and SystemOne POST never retry.
    A cascade attempt calls Jev once and catches its Astra fallback's errors.

    Helper (intent arm b): each ``analyze_request`` is one ``call_typesafe`` POST
    without retry, and a trial has at most ``max_rounds`` root rounds per run times
    ``1 + budget`` runs. The code does not cap parallel tool calls inside one round,
    so the helper cap assumes one analysis per round; more observed calls overrun the
    reservation and stop the program ledger (fail closed).
    """
    import ast

    def tree(relative: str) -> tuple[str, ast.Module]:
        text = (source / relative).read_text(encoding="utf-8")
        return text, ast.parse(text)

    _, loop_tree = tree("core/agent/loop/agent_loop.py")
    budget = _single(
        [
            node.value.value
            for node in ast.walk(loop_tree)
            if isinstance(node, ast.Assign)
            and any(
                isinstance(t, ast.Attribute) and t.attr == "_verify_continuation_budget"
                for t in node.targets
            )
            and isinstance(node.value, ast.Constant)
            and type(node.value.value) is int
        ],
        "AgenticLoop._verify_continuation_budget",
    )
    call_text, call_tree = tree("core/agent/loop/_provider_call.py")
    empty_attempts = _single(
        [
            node.value.value
            for node in call_tree.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(t, ast.Name) and t.id == "_FAIL_FAST_EMPTY_OUTPUT_MAX_ATTEMPTS"
                for t in node.targets
            )
            and isinstance(node.value, ast.Constant)
        ],
        "_FAIL_FAST_EMPTY_OUTPUT_MAX_ATTEMPTS",
    )
    if call_text.count("retrying the same adapter once") != 1:
        raise ValueError("cannot derive the Jev call cap: the single connection retry changed")
    agent_text, agent_tree = tree("evals/platforms/harbor_handoff.py")
    llm_retries = _single(
        [
            node.value.value
            for node in ast.walk(agent_tree)
            if isinstance(node, ast.Assign)
            and any(
                isinstance(t, ast.Attribute) and t.attr == "llm_max_retries" for t in node.targets
            )
            and isinstance(node.value, ast.Constant)
        ],
        "settings.llm_max_retries",
    )
    if (
        llm_retries != 1
        or 'os.environ["GEODE_LLM_FAIL_FAST_ON_ADAPTER_ERROR"] = "1"' not in agent_text
    ):
        raise ValueError("cannot derive the Jev call cap: the handoff agent retry policy changed")
    runtime_text, runtime_tree = tree("evals/benchmarks/decision_handoff_runtime.py")
    max_rounds = _single(
        [
            keyword.value.value
            for node in ast.walk(runtime_tree)
            if isinstance(node, ast.Call)
            and getattr(node.func, "id", getattr(node.func, "attr", "")) == "AgenticLoopConfig"
            for keyword in node.keywords
            if keyword.arg == "max_rounds" and isinstance(keyword.value, ast.Constant)
        ],
        "AgenticLoopConfig(max_rounds=...)",
    )
    clients = [
        node
        for node in ast.walk(runtime_tree)
        if isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "AsyncClient"
    ]
    if not clients or any(k.arg == "transport" for c in clients for k in c.keywords):
        raise ValueError("cannot derive the Jev call cap: the Jev HTTP client may retry")
    helper_text, _ = tree("evals/benchmarks/decision_handoff.py")
    if helper_text.count("await call_typesafe(") != 1:
        raise ValueError("cannot derive the Jev call cap: the helper dispatch path changed")
    judgments = 1 + int(budget)
    attempts = max(int(empty_attempts), 2)
    return {
        "judge_per_trial": judgments * attempts,
        "helper_per_trial": int(max_rounds) * judgments,
        "judgments_per_trial": judgments,
        "basis": {
            "verify_continuation_budget": int(budget),
            "fail_fast_empty_output_max_attempts": int(empty_attempts),
            "connection_retry_attempts": 2,
            "llm_max_retries": int(llm_retries),
            "max_rounds": int(max_rounds),
            "helper_assumption": "one analyze_request per root round (parallel calls are not capped in code)",
        },
    }
