"""One-time source pin of a private run folder (same schema as the intent runner).

``--pin-source --source <clean checkout> --revision <40-hex SHA>`` writes
``<run folder>/source-pin.json`` exactly once; every later mode, every dispatched
child and ``make_tasks.py`` read it. Stdlib only, no import of GEODE code.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

PIN_NAME = "source-pin.json"
PIN_SCHEMA = "geode.jev-runner-source-pin@1"
PIN_KEYS = frozenset({"schema", "source", "revision", "created_at"})
GIT = "/usr/bin/git"


def _git(checkout: Path, *args: str) -> str:
    return subprocess.run(  # noqa: S603 - fixed executable and arguments, no shell.
        [GIT, "-C", str(checkout), *args], check=True, capture_output=True, text=True
    ).stdout


def pin_source(root: Path, source: Path, revision: str) -> dict[str, str]:
    """Record the clean fixed-SHA checkout for this run folder; never overwrite."""
    if re.fullmatch(r"[0-9a-f]{40}", revision) is None:
        raise SystemExit("--revision must be a 40-character lowercase commit SHA")
    try:
        checkout = source.resolve(strict=True)
        toplevel = Path(_git(checkout, "rev-parse", "--show-toplevel").strip()).resolve()
        head = _git(checkout, "rev-parse", "HEAD").strip()
        dirty = _git(checkout, "status", "--porcelain")
    except (OSError, subprocess.CalledProcessError):
        raise SystemExit(f"--source is not a readable git checkout: {source}") from None
    if toplevel != checkout:
        raise SystemExit("--source must be the top level of its git checkout")
    if head != revision:
        raise SystemExit("--source HEAD does not match --revision")
    if dirty:
        raise SystemExit("--source checkout is dirty; pin a clean tree only")
    pin = {
        "schema": PIN_SCHEMA,
        "source": str(checkout),
        "revision": revision,
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    try:
        descriptor = os.open(root / PIN_NAME, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        raise SystemExit(f"{root / PIN_NAME} exists; a run folder is pinned exactly once") from None
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(pin, indent=2) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return pin


def load_source_pin(root: Path) -> tuple[Path, str]:
    """Fail closed unless the run folder carries one well-formed source pin."""
    path = root / PIN_NAME
    if path.is_symlink() or not path.is_file():
        raise SystemExit(
            f"source pin missing: {path}; first run: runner.py --pin-source "
            "--source <clean checkout> --revision <40-hex SHA>"
        )
    try:
        pin = json.loads(path.read_text(encoding="utf-8"))
        valid = (
            type(pin) is dict
            and set(pin) == PIN_KEYS
            and pin["schema"] == PIN_SCHEMA
            and type(pin["revision"]) is str
            and re.fullmatch(r"[0-9a-f]{40}", pin["revision"]) is not None
            and type(pin["source"]) is str
            and Path(pin["source"]).is_absolute()
            and datetime.fromisoformat(pin["created_at"]).utcoffset() == timedelta(0)
        )
    except (OSError, ValueError, TypeError):
        valid = False
    if not valid:
        raise SystemExit(f"source pin malformed: {path}")
    source = Path(pin["source"])
    if not source.is_dir() or source.resolve() != source:
        raise SystemExit(f"pinned source checkout missing or not canonical: {source}")
    return source, pin["revision"]


def clean_revision(source: Path) -> str:
    """HEAD of the pinned checkout; refuse a dirty tree before freeze or dispatch."""
    if _git(source, "status", "--porcelain"):
        raise ValueError("source is dirty; do not freeze or dispatch")
    return _git(source, "rev-parse", "HEAD").strip()
