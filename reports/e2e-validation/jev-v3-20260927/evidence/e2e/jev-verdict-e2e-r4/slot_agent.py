"""Handoff agent with an optional sibling start barrier (05 v2 §2.4, ``barrier_used``).

Harbor calls ``setup()`` under the 600 s setup timeout and ``run()`` under the
210 s agent timeout. The barrier waits at the end of ``setup()`` (after install
and credential upload), so waiting for a sibling never spends the root's 180 s
budget. Each arm writes ``<barrier_dir>/<arm>.ready``; an arm proceeds once every
peer is ready or its bound expires, and records ``<barrier_dir>/<arm>.json``.
Nothing here changes the frozen handoff profile, its model route or its checks.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any

from evals.platforms.harbor_handoff import GeodeHandoffHarborAgent

BARRIER_TIMEOUT_S = 120.0
SETUP_BUDGET_S = 600.0
SETUP_MARGIN_S = 15.0
POLL_S = 0.25


def _write_new(path: Path, value: Any) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(value, sort_keys=True) + "\n")


async def wait_for_peers(
    directory: Path,
    arm: str,
    peers: list[str],
    *,
    timeout_s: float,
    clock: Any = time.monotonic,
    wall: Any = time.time,
    poll_s: float = POLL_S,
) -> dict[str, Any]:
    """Announce readiness, wait for peers up to ``timeout_s``, return the receipt."""
    ready_wall = wall()
    _write_new(directory / f"{arm}.ready", {"arm": arm, "ready_at": ready_wall})
    started = clock()
    deadline = started + max(0.0, timeout_s)
    while True:
        seen = sorted(peer for peer in peers if (directory / f"{peer}.ready").is_file())
        if len(seen) == len(peers) or clock() >= deadline:
            break
        await asyncio.sleep(poll_s)
    receipt = {
        "arm": arm,
        "peers": sorted(peers),
        "peers_ready": seen,
        "ready_at": ready_wall,
        "released_at": wall(),
        "waited_s": round(clock() - started, 3),
        "timeout_s": timeout_s,
        "timed_out": len(seen) != len(peers),
    }
    _write_new(directory / f"{arm}.json", receipt)
    return receipt


class SlotBarrierHandoffAgent(GeodeHandoffHarborAgent):
    """``GeodeHandoffHarborAgent`` plus the slot barrier; its name stays geode-handoff."""

    def __init__(
        self,
        *args: Any,
        barrier_dir: str,
        barrier_arm: str,
        barrier_peers: list[str],
        barrier_timeout_sec: float = BARRIER_TIMEOUT_S,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        directory = Path(barrier_dir)
        if (
            not directory.is_absolute()
            or not directory.is_dir()
            or barrier_arm in barrier_peers
            or not barrier_peers
            or not 0 < barrier_timeout_sec <= BARRIER_TIMEOUT_S
        ):
            raise ValueError("slot barrier requires its slot directory, peers and a bound")
        self.barrier_dir = directory
        self.barrier_arm = barrier_arm
        self.barrier_peers = list(barrier_peers)
        self.barrier_timeout_sec = barrier_timeout_sec

    async def setup(self, environment: Any) -> None:
        entered = time.monotonic()
        await super().setup(environment)
        remaining = SETUP_BUDGET_S - SETUP_MARGIN_S - (time.monotonic() - entered)
        await wait_for_peers(
            self.barrier_dir,
            self.barrier_arm,
            self.barrier_peers,
            timeout_s=max(0.0, min(self.barrier_timeout_sec, remaining)),
        )
