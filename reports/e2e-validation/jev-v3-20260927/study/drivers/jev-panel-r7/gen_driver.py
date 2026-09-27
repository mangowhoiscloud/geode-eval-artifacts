"""Private G-track driver: natural candidate pools (U0b natural pool, U5p).

  --freeze --unit U --run-spec F --selection-dir <R>/panel-selection/selection
           [--task-template T] --reviewed
  --preflight --unit U
  --execute --unit U --reviewed [--quota-live]

For each frozen natural task (a selection cluster's inbox), GEODE's own
``delegate_task`` tool runs once with ``best_of=4``; the payload is frozen with
``score_selection.freeze_natural_pool`` (graded by the inbox oracle before any
selection) and never regenerated. Generation usage (sub-agent prompt/completion
tokens, the best-of judge block) is written to ``generation-usage.jsonl`` and the
quota ledger. Only U0b's natural workload IDs (those with a selection cluster
file) are generated here; its controlled pools are frozen elsewhere.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
from html import escape
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import track_common as tc  # noqa: E402

LOCAL_FILES = (
    "gen_driver.py",
    "track_common.py",
    "run_guards.py",
    "source_pin.py",
    "source-pin.json",
)
UNITS = {"U0b": "geode-jev-score-bestof-admission-", "U5p": "geode-jev-score-bestof-pool-"}
BEST_OF = 4
LOOKUP_LINES = (
    "For an unambiguous status request, fetch that item's intended order status with\n"
    "lookup_order_status. Batch all independent lookups in one call when useful.\n"
)
RECORD_LINES = (
    "For an unambiguous status request, read that item's intended order status from the\n"
    "order records below; they are the complete lookup results.\n"
)


def phase_dir(unit: str) -> Path:
    return HERE / f"{unit.lower()}-pool"


def driver_sha() -> str:
    return tc.sha(HERE / "gen_driver.py")


def natural_task(case: dict[str, Any], orders: dict[str, str], template: str | None = None) -> str:
    """The delegate task text: the inbox contract with the order records inline (no tools).

    Default: the E2E inbox contract (``INBOX_SYSTEM``) with its lookup sentence
    replaced by inline order records, then the public inbox (never labels). A
    reviewed ``--task-template`` (``{contract}``, ``{orders}``, ``{inbox}``) replaces it.
    """
    from evals.benchmarks.decision_handoff_runtime import INBOX_SYSTEM, inbox_request

    if INBOX_SYSTEM.count(LOOKUP_LINES) != 1:
        raise ValueError("the inbox contract changed; review the natural task text")
    contract = INBOX_SYSTEM.replace(LOOKUP_LINES, RECORD_LINES).replace(
        "Do not claim completion without consuming the required lookup observations.\n", ""
    )
    records = (
        "<order_records>"
        + escape(json.dumps(orders, ensure_ascii=False, sort_keys=True))
        + "</order_records>"
    )
    inbox = inbox_request(case["items"])
    if template is not None:
        return template.format(contract=contract, orders=records, inbox=inbox)
    return f'{contract}\n{records}\n{inbox}\nReturn only one JSON object {{"items": [...]}}.'


def load_case(selection_dir: Path, cluster_id: str) -> tuple[dict[str, Any], dict[str, str]]:
    """A selection cluster's inbox case and orders (public split; no gold beyond the case)."""
    from evals.benchmarks.decision_handoff_runtime import inbox_request, validate_inbox_case

    document = tc.read(selection_dir / f"{cluster_id}.json")
    if document.get("cluster_id") != cluster_id:
        raise ValueError(f"{cluster_id}: cluster file mismatch")
    items = document["case"]["items"]
    case = {"id": cluster_id, "profile": "inbox", "items": items, "request": inbox_request(items)}
    orders = dict(document["orders"])
    validate_inbox_case(case, orders)
    return case, orders


def natural_ids(unit: str, ids: list[str], selection_dir: Path) -> list[str]:
    chosen = [i for i in ids if (selection_dir / f"{i}.json").is_file()] if unit == "U0b" else ids
    if not chosen or (unit == "U5p" and chosen != ids):
        raise ValueError(f"{unit}: natural workloads must be selection clusters")
    return chosen


def build_cells(tasks: list[dict[str, Any]], source: Path, revision: str) -> list[dict[str, Any]]:
    verifier = tc.sha(source / "evals/benchmarks/score_selection.py")
    cells = []
    for task in tasks:
        policy = {
            "tool": "delegate_task",
            "best_of": BEST_OF,
            "route": tc.ASTRA_ROUTE,
            "candidate_chars": 2000,
            "regenerate": "never; one payload per task",
            "source_revision": revision,
        }
        cells.append(
            {
                "index": len(cells),
                "pool_id": task["pool_id"],
                "cluster_id": task["cluster_id"],
                **tc.cell_digests(
                    policy,
                    case_sha256=hashlib.sha256(tc.canonical(task["case"]).encode()).hexdigest(),
                    task_checksum=hashlib.sha256(task["task"].encode()).hexdigest(),
                    verifier_sha256=verifier,
                ),
            }
        )
    return cells


def freeze(
    unit: str, spec_path: Path, selection_dir: Path, template_path: Path | None
) -> dict[str, Any]:
    import source_pin
    from scripts.eval.contract import validate_run_spec

    source, revision = tc.pinned_source()
    if source_pin.clean_revision(source) != revision:
        raise ValueError("pinned checkout moved")
    spec = validate_run_spec(spec_path)
    concurrency = spec["reproduction"]["execution"]["max_concurrency"]
    ids = tc.check_spec(
        spec,
        prefix=UNITS[unit],
        revision=revision,
        driver_sha256=driver_sha(),
        max_concurrency=concurrency,
    )
    template_bytes = template_path.read_bytes() if template_path else None
    references = [
        entry.strip()
        for entry in spec["reproduction"]["environment"]["initial_state_ref"].split(";")
        if "natural-task.template.txt" in entry
    ]
    if references and (
        template_bytes is None
        or references
        != [f"natural-task.template.txt sha256:{hashlib.sha256(template_bytes).hexdigest()}"]
    ):
        raise ValueError("--task-template bytes must match the run-spec natural-task template SHA")
    template = template_bytes.decode("utf-8") if template_bytes is not None else None
    tasks = []
    for cluster_id in natural_ids(unit, ids, selection_dir):
        case, orders = load_case(selection_dir, cluster_id)
        tasks.append(
            {
                "pool_id": cluster_id,
                "cluster_id": cluster_id,
                "case": case,
                "orders": orders,
                "task": natural_task(case, orders, template),
            }
        )
    directory = phase_dir(unit)
    directory.mkdir(mode=0o700)
    copy = directory / "run-spec.json"
    tc.write_new(copy, spec_path.read_text(encoding="utf-8"))
    inputs = [
        copy,
        *(selection_dir.resolve() / f"{t['cluster_id']}.json" for t in tasks),
        *(HERE / n for n in LOCAL_FILES),
    ]
    inputs += [template_path.resolve()] if template_path else []
    inputs += [
        source / "evals/benchmarks/score_selection.py",
        source / "evals/benchmarks/decision_handoff_runtime.py",
    ]
    record = {
        "schema": "jev-v3.generation-freeze@1",
        "unit": unit,
        "run_id": spec["run_id"],
        "frozen_at": tc.now(),
        "source_revision": revision,
        "selection_dir": str(selection_dir.resolve()),
        "task_template": str(template_path.resolve()) if template_path else None,
        "tasks": [{k: t[k] for k in ("pool_id", "cluster_id", "task")} for t in tasks],
        "cells": build_cells(tasks, source, revision),
        "best_of": BEST_OF,
        "planned_astra_call_cap": spec["reproduction"]["execution"]["budget"]["limit"],
        "driver_sha256": driver_sha(),
        "sha256": tc.bound_inputs(inputs),
    }
    tc.write_new(directory / "freeze.json", record)
    print(f"{unit}: frozen {len(tasks)} natural tasks, best_of={BEST_OF}; no model call")
    return record


def preflight(unit: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
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
    template = (
        Path(frozen["task_template"]).read_bytes().decode("utf-8")
        if frozen["task_template"]
        else None
    )
    tasks = []
    for entry in frozen["tasks"]:
        case, orders = load_case(Path(frozen["selection_dir"]), entry["cluster_id"])
        if natural_task(case, orders, template) != entry["task"]:
            raise ValueError(f"{entry['pool_id']}: frozen task text changed")
        tasks.append({**entry, "case": case, "orders": orders})
    if build_cells(tasks, source, revision) != frozen["cells"]:
        raise ValueError(f"{unit}: frozen cells changed")
    return frozen, tasks


def real_delegate(run_id: str) -> Any:
    """The native best-of path with frozen Astra routing and no candidate tools."""
    import core

    from core.agent.sub_agent import SubAgentManager
    from core.agent.tool_executor.executor import ToolExecutor
    from core.config import settings
    from core.config.policy_source import EMPTY_POLICY_SOURCES
    from core.orchestration.isolated_execution import IsolatedRunner
    from core.skills.agents import AgentRegistry
    from core.tools.base import ToolContext
    from core.tools.toolkit_registry import load_default_registry
    from evals.run_timeline import current_run_timeline

    source, _ = tc.pinned_source()
    # IsolatedRunner starts ``python -m evals.worker`` without changing cwd.
    # Parent sys.path insertion alone does not pin a fresh child interpreter.
    if Path.cwd().resolve() != source or not Path(core.__file__).resolve().is_relative_to(source):
        raise ValueError("G execution must start from the pinned source checkout")
    for field in ("judge_model", "cognitive_reflection_model", "act_model"):
        if getattr(settings, field).strip():
            raise ValueError(f"G requires inherited Astra routing; clear {field} before freezing")

    registry = AgentRegistry()
    registry.load_defaults()
    agent = registry.get("data_analyst")
    if agent is None or agent.toolkit != "data_analysis" or agent.model:
        raise ValueError("the bundled generation agent changed; review before freezing")
    # Keep the original bundled system prompt and native diversity lenses.
    # An empty whitelist would fall back to _default tools, so deny every
    # tool in the named toolkit instead (the worker enforces the denial).
    denied = set(load_default_registry().resolve(agent.toolkit))
    if not denied:
        raise ValueError("the generation toolkit is missing; review before freezing")

    async def delegate(task: str, pool_id: str) -> dict[str, Any]:
        # Each pool is an independent best-of-4 run. A unit-wide manager's
        # default 15-child cap would truncate the fourth of U5p's 12 pools.
        manager = SubAgentManager(
            IsolatedRunner(hooks=None, lane=None, worker_module="evals.worker"),
            action_handlers={},
            agent_registry=registry,
            hooks=None,
            max_depth=settings.max_subagent_depth,
            denied_tools=denied,
            activity_sink_provider=current_run_timeline,
            policy_sources=EMPTY_POLICY_SOURCES,
            timeout_s=1800.0,
        )
        executor = ToolExecutor(
            sub_agent_manager=manager,
            auto_approve=True,
            interactive_approval=False,
            allowed_tools=frozenset({"delegate_task"}),
        )
        context = ToolContext(
            session_id=run_id,
            turn_id=f"{run_id}:{pool_id}",
            tool_call_id=f"gen-{pool_id}",
            provider="openai",
            source="subscription",
            model="gpt-6-astra",
            effort="xhigh",
        )
        return await executor.aexecute(
            "delegate_task",
            {
                "task_description": task,
                "task_type": "analyze",
                "model": "gpt-6-astra",
                "source": "subscription",
                "best_of": BEST_OF,
            },
            context=context,
        )

    return delegate


def usage_row(pool_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Observed generation usage; SubResult zeros stay as reported (unreported may be 0)."""
    rows = payload.get("tasks") if isinstance(payload.get("tasks"), list) else []
    best = payload.get("best_of") if isinstance(payload.get("best_of"), dict) else {}
    return {
        "pool_id": pool_id,
        "candidates": [
            {
                k: row.get(k)
                for k in (
                    "task_id",
                    "success",
                    "prompt_tokens",
                    "completion_tokens",
                    "usd_spent",
                    "duration_ms",
                )
            }
            for row in rows
        ],
        "judge": {k: v for k, v in best.items() if k not in {"reason", "output", "text"}},
        "prompt_tokens_sum": sum(int(row.get("prompt_tokens") or 0) for row in rows),
        "completion_tokens_sum": sum(int(row.get("completion_tokens") or 0) for row in rows),
        "calls_basis": "sub-agent runs + one best-of judge; inner loop rounds are not counted",
    }


async def execute(unit: str, *, quota_live: bool, delegate: Any = None) -> int:
    from core.observability.run_dir import run_dir_scope
    from evals.benchmarks.score_selection import freeze_natural_pool, pool_record

    frozen, tasks = preflight(unit)
    directory = phase_dir(unit)
    admission = tc.admit(
        directory,
        unit=f"{unit}-gen",
        run_id=frozen["run_id"],
        lock_mode="gen",
        planned_astra=frozen["planned_astra_call_cap"],
        planned_jev=0,
        required_margin_s=int(len(tasks) * 1800 + tc.AUTH_MARGIN_SLACK_S),
        quota_live=quota_live,
    )
    if admission is None:
        return 3
    # One quota reading at mid-unit (05 §7: U5p is checked once in the middle).
    control = tc.CallControl(
        admission, reader=tc.live_snapshot if quota_live else None, every=len(tasks) // 2 + 1
    )
    stop, calls, tokens, frozen_pools = None, 0, 0, 0
    try:
        tc.pin_runtime_settings()
        run = delegate or real_delegate(frozen["run_id"])
        for task in tasks:
            reason = control.before_call("llm")  # one reading at mid-unit for U5p (05 §7)
            if reason is not None:
                stop = reason
                tc.stop_unit(directory, reason, "in-unit guard stopped generation")
                break
            with run_dir_scope(directory):
                payload = await run(task["task"], task["pool_id"])
            tc.write_new(directory / "payloads" / f"{task['pool_id']}.json", payload)
            usage = usage_row(task["pool_id"], payload)
            tc.append_jsonl(directory / "generation-usage.jsonl", usage)
            calls += len(usage["candidates"]) + 1
            tokens += usage["prompt_tokens_sum"]
            try:
                pool = freeze_natural_pool(
                    pool_id=task["pool_id"],
                    task=task["task"],
                    case=task["case"],
                    orders=task["orders"],
                    payload=payload,
                    cluster_id=task["cluster_id"],
                )
            except ValueError as error:
                tc.append_jsonl(
                    directory / "pool-errors.jsonl",
                    {"pool_id": task["pool_id"], "error": str(error)},
                )
                continue
            tc.append_jsonl(directory / "pools.natural.jsonl", pool_record(pool))
            frozen_pools += 1
        tc.block_receipt(
            admission,
            block_id=f"{unit}-generation",
            lock_mode="gen",
            source_revision=frozen["source_revision"],
            freeze_sha256=tc.sha(directory / "freeze.json"),
            extra={
                "planned_tasks": len(tasks),
                "frozen_pools": frozen_pools,
                "stop_reason": stop,
                "generation_prompt_tokens": tokens,
            },
        )
    finally:
        admission.close(astra_calls=calls, astra_input_tokens=tokens)
        tc.assert_no_secret(directory, [])
    print(json.dumps({"unit": unit, "frozen_pools": frozen_pools, "stop_reason": stop}))
    return 0 if stop is None and frozen_pools == len(tasks) else 1


def main(argv: list[str] | None = None) -> int:
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--freeze", action="store_true")
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--unit", choices=sorted(UNITS), required=True)
    parser.add_argument("--run-spec", type=Path)
    parser.add_argument("--selection-dir", type=Path)
    parser.add_argument("--task-template", type=Path)
    parser.add_argument("--reviewed", action="store_true")
    parser.add_argument("--quota-live", action="store_true", help="user-approved WHAM lookup")
    args = parser.parse_args(argv)
    if args.freeze:
        if not (args.reviewed and args.run_spec and args.selection_dir):
            parser.error("--freeze needs --run-spec, --selection-dir and --reviewed")
        freeze(args.unit, args.run_spec, args.selection_dir, args.task_template)
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
