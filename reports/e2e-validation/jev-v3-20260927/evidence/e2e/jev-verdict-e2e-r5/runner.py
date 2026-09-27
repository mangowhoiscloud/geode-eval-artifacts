"""Jev v3 paired-slot Harbor E2E runner: U0d, U0e, U0f, U7r0, U7r1, U8c, U8n.

Private run-folder code (05 v2 §2.4-§2.6, §4.3, §7, §9). Only ``--execute
--reviewed`` dispatches models; every other mode is model-free.

  --pin-source --source <clean checkout> --revision <sha>     once per run folder
  --self-test                                                 offline logic and mock slots
  --infra-preflight --concurrency N --reviewed                Docker only, no model
  --quota-snapshot --used-pct P --checkpoint ID [...]         record a /status reading
  --freeze --unit U --run-spec F --bundle B [--arm-c --selection-freeze S] [--barrier] --reviewed
  --preflight --unit U
  --execute --unit U --reviewed [--quota-live]
  --child --unit U --index N [--secret-file F]                internal, one arm

A slot launches every compared arm at once (A/B, or A/B/C once arm C is
approved), then waits until each arm exits and is collected with its cleanup
verified before the next slot starts. The host execution lock keeps E, P, G and
solo tracks from overlapping. Account, quota and Jev-budget guards refuse a slot
before launch; infrastructure-invalid arms stop the unit after their siblings.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib
import importlib.metadata
import importlib.util
import json
import os
import signal
import statistics
import sys
import tarfile
import time
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
RUN_ROOT = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import source_pin  # noqa: E402

if __name__ == "__main__" and "--pin-source" in sys.argv[1:]:
    _pin = argparse.ArgumentParser(description="Write this run folder's source pin once.")
    _pin.add_argument("--pin-source", action="store_true", required=True)
    _pin.add_argument("--source", type=Path, required=True)
    _pin.add_argument("--revision", required=True)
    _arguments = _pin.parse_args()
    os.umask(0o077)
    ROOT.chmod(0o700)
    source_pin.pin_source(ROOT, _arguments.source, _arguments.revision)
    print(f"Pinned {_arguments.revision}; no archive, Docker, credential or model access")
    raise SystemExit(0)

from paired_dispatch import (  # noqa: E402
    ARM_LABELS,
    PREVIEW_SOURCES,
    ArmRun,
    PairedDispatcher,
    Slot,
    SlotReport,
    SubprocessDriver,
    UnitReport,
    agent_interval,
    load_slots,
    prebuild_images,
)
from run_guards import (  # noqa: E402
    AUTH_MARGIN_SLACK_S,
    EXPECTED_ACCOUNT_FP12,
    EXPECTED_PLAN,
    ExecutionLock,
    QuotaLedger,
    QuotaSnapshot,
    ScheduleOverlapError,
    account_fields,
    account_refusal,
    codex_auth_file,
    derive_jev_call_caps,
    latest_snapshot,
    live_snapshot,
    read_account_claims,
    record_snapshot,
)
from slot_guards import (  # noqa: E402
    AccountGuard,
    JevGuard,
    LockGuard,
    PreflightGuard,
    QuotaGuard,
    StopFileGuard,
    private_receipt,
    write_private_receipt,
)

SOURCE, REVISION = source_pin.load_source_pin(ROOT)
LEGACY_ROOT = Path("withheld-local-path-f40f68724bf591b3")
PINS = {
    "runner.py": "2c1b1427e7634cadd2969464fd532915bdbcbec20e3840d1e538a813e69f1f40",
    "make_tasks.py": "2efc952c9723392455a92b6562f2a45f5d67aa1019fae0958ce6440e9658869d",
}
SLOTS = ROOT / "e2e-slots.jsonl"
MANIFEST = ROOT / "payload-manifest.json"
SOURCES = ROOT / "e2e-sources.json"
INFRA = ROOT / "infrastructure"
QUOTA_LEDGER = RUN_ROOT / "quota-ledger.csv"
JEV_LEDGER = RUN_ROOT / "jev-cost-ledger.jsonl"
# 05-budget-amendment: inherited quantum times initial + two verification turns.
ROOT_BUDGET = 180 * (1 + 2)
AGENT_BUDGET = ROOT_BUDGET + (210 - 180)
WATCHDOG = 930.0 + (ROOT_BUDGET - 180)
CLEANUP = 120.0
SNAPSHOT_MAX_AGE_S = 3600.0
LOCAL_FILES = (
    "runner.py",
    "paired_dispatch.py",
    "run_guards.py",
    "slot_agent.py",
    "slot_guards.py",
    "source_pin.py",
    "make_tasks.py",
    "self_test.py",
    "protocol.md",
    "source-pin.json",
    "e2e-slots.jsonl",
    "e2e-sources.json",
)
RUN_ID_PREFIX = {
    "U0d": "geode-jev-verdict-e2e-admission-",
    "U0e": "geode-jev-noul-verdict-admission-",
    "U0f": "geode-jev-verdict-e2e-cascade-admission-",
    "U7r0": "geode-jev-verdict-e2e-natural-r0-",
    "U7r1": "geode-jev-verdict-e2e-natural-r1-",
    "U8c": "geode-jev-verdict-e2e-injection-",
    "U8n": "geode-jev-noul-verdict-conditions-",
}
UNITS: dict[str, dict[str, Any]] = {
    "U0d": {
        "kind": "admission",
        "primitive": "choice",
        "metric": "verdict_e2e_admission_success",
        "denominator": 4,
        "needs": (),
    },
    "U0e": {
        "kind": "admission",
        "primitive": "noul",
        "metric": "noul_e2e_admission_success",
        "denominator": 2,
        "needs": (),
    },
    "U0f": {
        "kind": "admission",
        "primitive": "choice",
        "metric": "cascade_e2e_admission_success",
        "denominator": 2,
        "needs": ("U0d",),
    },
    "U7r0": {
        "kind": "natural",
        "primitive": "choice",
        "metric": "m8n_strict_success_delta",
        "denominator": 12,
        "needs": ("U0d",),
    },
    "U7r1": {
        "kind": "natural",
        "primitive": "choice",
        "metric": "m8n_strict_success_delta",
        "denominator": 12,
        "needs": ("U0d", "U7r0"),
    },
    "U8c": {
        "kind": "injected",
        "primitive": "choice",
        "metric": "m8i_choice_recovery_delta",
        "denominator": 18,
        "needs": ("U0d",),
    },
    "U8n": {
        "kind": "injected",
        "primitive": "noul",
        "metric": "m8i_noul_recovery_delta",
        "denominator": 18,
        "needs": ("U0e",),
    },
}
RESET_BOUNDARY = {
    "session": "fresh GEODE_HOME and session store inside a new agent container per trial",
    "files": "new public-network agent container and a separate no-network verifier per trial; "
    "no operator workspace mount; task files only from the frozen bundle",
    "cache": "no local cache shared across trials; provider-side prompt caching is not "
    "controlled and stays unknown",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_pinned(name: str) -> Any:
    path = LEGACY_ROOT / name
    if sha(path) != PINS[name]:
        raise ValueError("reused orchestration source changed: " + name)
    spec = importlib.util.spec_from_file_location("jev_v3_" + path.stem, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sys.path.insert(0, str(SOURCE))
importlib.import_module("evals.platforms.harbor_docker")
base = load_pinned("runner.py")
if str(base.SOURCE) in sys.path:
    sys.path.remove(str(base.SOURCE))
base.ROOT, base.SOURCE = ROOT, SOURCE
ObservedDockerEnvironment = base.ObservedDockerEnvironment
read, write, append, now = base.read, base.write, base.append, base.now


def phase_dir(unit: str) -> Path:
    return ROOT / unit.lower()


def slot_rows() -> list[dict[str, Any]]:
    return [json.loads(line) for line in SLOTS.read_text(encoding="utf-8").splitlines() if line]


def _digest(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def cell_policy(
    cell: Mapping[str, Any], *, task_checksum: str, verifier_sha256: str
) -> dict[str, Any]:
    """Everything that must be equal for repetitions to combine (03 §5.1)."""
    from evals.benchmarks.decision_handoff_runtime import INBOX_SYSTEM
    from evals.benchmarks.decision_verification import contract_digests

    engine = cell["verification_engine"]
    judge = {
        "llm": "openai/subscription/gpt-6-astra/xhigh",
        "jev": "typesafe/payg/jev-1.13.0/none",
        "cascade": f"jev-1.13.0 first, q>=tau {cell['cascade_tau']}, else openai/subscription/gpt-6-astra/xhigh",
    }[engine]
    policy = {
        "root_route": "openai/subscription/gpt-6-astra/xhigh",
        "reflection_route": "openai/subscription/gpt-6-astra/xhigh",
        "final_judge": judge,
        "judge_primitive": cell["verification_primitive"],
        "judge_contract": contract_digests(cell["verification_primitive"]),
        "task_contract_sha256": hashlib.sha256(INBOX_SYSTEM.encode()).hexdigest(),
        "tools": "lookup_order_status (read-only)",
        "task_checksum": task_checksum,
        "verifier_sha256": verifier_sha256,
        "budget": f"root {ROOT_BUDGET}s/6 rounds; agent {AGENT_BUDGET}s; setup 600s; verifier 30s; watchdog {WATCHDOG:g}s; cleanup 120s",
        "repair_limit": "frozen runtime verify continuation budget",
        "llm_max_retries": "1",
        "source_revision": REVISION,
    }

    if cell["unit"] in {"U7r0", "U7r1"}:
        # Task-specific digests are separate frozen-cell contract fields.
        # The reliability owner requires one policy digest across an arm.
        policy.pop("task_checksum")
        policy.pop("verifier_sha256")
    return policy


def build_cells(
    unit: str,
    slots: Sequence[Slot],
    manifest: Mapping[str, Any],
    *,
    tau: str | None,
    barrier: bool,
) -> list[dict[str, Any]]:
    """Frozen cells in dispatch order: slot-major, frozen launch order within a slot."""
    config = UNITS[unit]
    entries = {entry["workload_id"]: entry for entry in manifest["workloads"]}
    cells: list[dict[str, Any]] = []
    for slot in slots:
        entry = entries.get(slot.workload_id)
        if entry is None:
            raise ValueError(f"{slot.slot_id}: task bundle lacks {slot.workload_id}")
        if (slot.cell != "natural") != bool(entry["verification_intervention"]):
            raise ValueError(f"{slot.slot_id}: payload intervention does not match its cell")
        for position, arm in enumerate(slot.launch_order):
            cells.append(
                {
                    "index": len(cells),
                    "unit": unit,
                    "slot_id": slot.slot_id,
                    "slot_index": slot.slot_index,
                    "workload_id": slot.workload_id,
                    "cluster_id": slot.task,
                    "cell": slot.cell,
                    "case_id": entry["case_id"],
                    "repetition": slot.repetition,
                    "position": position,
                    "arm": arm.lower(),
                    "arm_letter": arm,
                    "verification_engine": ARM_LABELS[arm],
                    "verification_primitive": config["primitive"],
                    "cascade_tau": tau if arm == "C" else None,
                    "uses_jev": arm in ("B", "C"),
                    "barrier": barrier and len(slot.arms) > 1,
                    "task_dir": str(ROOT / entry["task_dir"]),
                    "case_file": str(ROOT / entry["case_file"]),
                    "trial_name": f"jev3-{unit.lower()}-r{slot.repetition}-{slot.task}-{slot.cell}-{arm.lower()}",
                    "replay_preselected": slot.replay_preselected,
                    "replay_side": slot.replay_side(arm),
                    "noul_truth": entry["noul_truth"],
                }
            )
    if len({cell["trial_name"] for cell in cells}) != len(cells):
        raise ValueError("trial names repeat")
    return cells


def unit_slots(unit: str, *, arm_c: bool) -> list[Slot]:
    slots = load_slots(slot_rows(), unit, arm_c=arm_c)
    if unit == "U7r1":
        earlier = load_slots(slot_rows(), "U7r0", arm_c=arm_c)
        if [slot.task for slot in slots] != [slot.task for slot in earlier]:
            raise ValueError("U7r1 must repeat U7r0's tasks in the same order")
    if unit == "U8n":
        paired = load_slots(slot_rows(), "U8c", arm_c=False)
        if [s.workload_id for s in slots] != [s.workload_id for s in paired]:
            raise ValueError("U8n must use U8c's task-cells in the same order")
    return slots


# --- infrastructure ------------------------------------------------------------


async def infrastructure(concurrency: int) -> dict[str, Any]:
    """Model-free proof: N agent/verifier environment pairs started concurrently.

    Each pair checks the agent's public network, the verifier's missing egress and
    cleanup. The proof lets a unit with at most N arms freeze and dispatch for 24h.
    """
    from harbor.environments.factory import EnvironmentFactory
    from harbor.models.task.task import Task
    from harbor.models.trial.config import EnvironmentConfig
    from harbor.models.trial.paths import TrialPaths

    if not 2 <= concurrency <= 3:
        raise ValueError("paired slots need 2 (or 3 with arm C) concurrent trials")
    INFRA.mkdir(mode=0o700, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    manifest = read(MANIFEST)
    task = Task(ROOT / manifest["workloads"][0]["task_dir"])
    environments: list[Any] = []
    observations: list[dict[str, Any]] = []
    error = None

    async def pair(index: int) -> None:
        paths = TrialPaths(trial_dir=INFRA / f"native-{stamp}-{index}")
        paths.mkdir()
        for role, config, environment_dir in (
            ("agent", task.config.environment, task.paths.environment_dir),
            ("verifier", task.config.verifier.environment, task.paths.tests_dir),
        ):
            policy = config.resolve_baseline()
            env = EnvironmentFactory.create_environment_from_config(
                config=EnvironmentConfig(
                    import_path="runner:ObservedDockerEnvironment", delete=True
                ),
                environment_dir=environment_dir,
                environment_name=task.short_name,
                session_id=f"jev3-infra-{stamp}-{index}-{role}",
                trial_paths=paths,
                task_env_config=config,
                mounts=[],
                network_policy=policy,
                phase_network_policies=[policy],
            )
            environments.append(env)
            await asyncio.wait_for(env.start(force_build=False), timeout=600)
            output = await env.exec(
                command="python -c " + base.shlex.quote(base.NETWORK_SCRIPT), timeout_sec=20
            )
            assert output.return_code == 0
            check = base.inspect_network(json.loads(output.stdout), offline=role == "verifier")
            record = {"pair": index, "role": role, "session_id": env.session_id, "network": check}
            if role == "verifier":
                probe = (
                    "import errno,socket\ns=socket.socket();s.settimeout(2)\n"
                    "try:s.connect(('192.0.2.1',443))\nexcept OSError as e:assert e.errno==errno.ENETUNREACH\n"
                    "else:raise AssertionError('egress allowed')\nfinally:s.close()"
                )
                denied = await env.exec(
                    command="python -c " + base.shlex.quote(probe), timeout_sec=10
                )
                assert denied.return_code == 0
                record["egress_denied"] = True
            observations.append(record)

    started = time.time()
    prebuilt: list[dict[str, Any]] = []
    try:
        # Every task a slot can use is built or pulled once, serially, before any pair.
        prebuilt = await prebuild_images(
            sorted(dict.fromkeys(ROOT / w["task_dir"] for w in manifest["workloads"]))
        )
        await asyncio.gather(*(pair(index) for index in range(concurrency)))
    except BaseException as exc:
        error = type(exc).__name__
    finally:
        cleanup_errors = []
        for env in reversed(environments):
            try:
                await asyncio.wait_for(env.stop(delete=True), timeout=CLEANUP)
            except BaseException as exc:
                cleanup_errors.append(type(exc).__name__)
        cleanup = [base.resources_for_session(env.session_id) for env in environments]
    passed = (
        error is None
        and len(observations) == 2 * concurrency
        and not cleanup_errors
        and all(row["complete"] for row in cleanup)
    )
    proof = {
        "schema": "jev-v3.infra-proof@1",
        "passed": passed,
        "model_dispatches": 0,
        "concurrency": concurrency,
        "source_revision": source_pin.clean_revision(SOURCE),
        "started_at": datetime.fromtimestamp(started, tz=UTC).isoformat(),
        "finished_at": now(),
        "daemon": base.daemon_identity(),
        "prebuilt_images": prebuilt,
        "observations": observations,
        "cleanup": cleanup,
        "cleanup_errors": cleanup_errors,
        "error_type": error,
        "task_manifest_sha256": sha(MANIFEST),
    }
    write(INFRA / f"proof-{stamp}.json", proof)
    if not passed:
        raise SystemExit("infrastructure proof failed; see " + str(INFRA / f"proof-{stamp}.json"))
    return proof


def require_infrastructure(minimum_concurrency: int) -> tuple[Path, dict[str, Any]]:
    """Newest passing proof (<24h) for this source, bundle, daemon and slot width."""
    proofs = sorted(INFRA.glob("proof-*.json")) if INFRA.is_dir() else []
    if not proofs:
        raise ValueError("no infrastructure proof; run --infra-preflight today")
    path = proofs[-1]
    proof = read(path)
    age = (datetime.now(UTC) - datetime.fromisoformat(proof["finished_at"])).total_seconds()
    if not (
        proof["passed"] is True
        and proof["model_dispatches"] == 0
        and 0 <= age < 86400
        and proof["concurrency"] >= minimum_concurrency
        and proof["source_revision"] == REVISION
        and proof["task_manifest_sha256"] == sha(MANIFEST)
        and proof["daemon"] == base.daemon_identity()
        and {row["task"] for row in proof.get("prebuilt_images", []) if row["role"] == "verifier"}
        >= {Path(w["task_dir"]).name for w in read(MANIFEST)["workloads"]}
    ):
        raise ValueError(f"infrastructure proof {path.name} is stale, failed or too narrow")
    return path, proof


# --- freeze and preflight -------------------------------------------------------


def required_units(unit: str, *, arm_c: bool) -> tuple[str, ...]:
    """Dependencies (05 v2 §2.5, §6): arm C in U7 also needs a passed U0f."""
    needs = tuple(UNITS[unit]["needs"])
    return (*needs, "U0f") if arm_c and unit in {"U7r0", "U7r1"} else needs


def _check_admission(unit: str, *, arm_c: bool) -> dict[str, str]:
    """Earlier units a unit depends on must be complete; admissions need reviewed playback."""
    from scripts.eval.contract import validate_run_bundle

    bound: dict[str, str] = {}
    for needed in required_units(unit, arm_c=arm_c):
        directory = phase_dir(needed)
        validate_run_bundle(directory / "run-spec.json")
        result = read(directory / "results.json")
        frozen = read(directory / "freeze.json")
        if frozen["source_revision"] != REVISION or result["complete"] is not True:
            raise ValueError(f"{unit} needs a complete {needed} on the same source")
        if UNITS[needed]["kind"] == "admission":
            if result["primary"]["numerator"] != UNITS[needed]["denominator"]:
                raise ValueError(f"{needed} admission did not pass every cell")
            playback = read(directory / "playback-check.json")
            casts = {
                f"trials/{cell['trial_name']}/agent/recording.cast" for cell in frozen["cells"]
            }
            if (
                playback.get("played") is not True
                or playback.get("score_authority") is not False
                or playback.get("source_revision") != REVISION
                or playback.get("admission_results_sha256") != sha(directory / "results.json")
                or {item["path"] for item in playback.get("recordings", [])} != casts
                or any(
                    sha(directory / item["path"]) != item["sha256"]
                    for item in playback["recordings"]
                )
            ):
                raise ValueError(f"{needed}: reviewed playback approval is missing or stale")
            bound[str(directory / "playback-check.json")] = sha(directory / "playback-check.json")
        for name in (
            "run-spec.json",
            "freeze.json",
            "results.json",
            "attempts.jsonl",
            "analysis.json",
        ):
            bound[str(directory / name)] = sha(directory / name)
    return bound


def _selection_tau(path: Path) -> str:
    from evals.benchmarks.decision_cascade import cascade_tau_from_selection

    document = read(path)
    if document.get("schema_id") != "geode.jev-selection-freeze@1":
        raise ValueError("selection freeze schema mismatch")
    return cascade_tau_from_selection(document["cascade"]["tau"])


def _check_task(cell: dict[str, Any], manifest: Mapping[str, Any]) -> None:
    from evals.platforms.harbor_handoff import _task
    from harbor.models.task.task import Task

    task_dir = Path(cell["task_dir"])
    task = Task(task_dir)
    payload = _task(Path(cell["case_file"]), sha(Path(cell["case_file"])))
    config = task.config
    if not (
        task_dir.resolve().is_relative_to((ROOT / "task-bundle").resolve())
        and Path(cell["case_file"]).resolve().is_relative_to((ROOT / "payloads").resolve())
        and task.instruction == payload["case"]["request"]
        and payload["case"] == read(task_dir / "tests/case.json")
        and payload["case"]["id"] == cell["case_id"]
        and ("verification_intervention" in payload) == (cell["cell"] != "natural")
        and str(config.environment.docker_image) == manifest["image_digest"]
        and config.agent.timeout_sec == AGENT_BUDGET
        and config.verifier.timeout_sec == 30
        and config.verifier.environment is not None
        and not task.has_steps
        and config.verifier.environment.network_mode == config.verifier.network_mode == "no-network"
        and config.environment.network_mode == "public"
        and tuple(config.artifacts) == base.TRANSFER
        and sha(task_dir / "tests/handoff_runtime.py")
        == sha(SOURCE / "evals/benchmarks/decision_handoff_runtime.py")
        and sha(task_dir / "tests/requirements.txt") == manifest["verifier_requirements_sha256"]
    ):
        raise ValueError(f"{cell['trial_name']}: frozen task or payload contract mismatch")
    cell.update(
        task_name=task.name,
        task_checksum=task.checksum,
        case_sha256=sha(Path(cell["case_file"])),
        verifier_sha256=sha(task_dir / "tests/verify.py"),
    )


def _check_spec(unit: str, spec: Mapping[str, Any], slots: Sequence[Slot]) -> None:
    config = UNITS[unit]
    execution = spec["reproduction"]["execution"]
    primary = spec["study"]["primary_metric"]
    suffix = spec["run_id"].removeprefix(RUN_ID_PREFIX[unit])
    if not (
        spec["run_id"].startswith(RUN_ID_PREFIX[unit])
        and suffix[:8].isdigit()
        and suffix[8:] in {""} | {f"-r{n}" for n in range(1, 10)}
        and spec["reproduction"]["geode"]["revision"] == REVISION
        and spec["reproduction"]["geode"]["dirty"] is False
        and spec["reproduction"]["model"]
        == {
            "provider": "openai",
            "label": "gpt-6-astra",
            "route": "subscription",
            "reasoning": "xhigh",
        }
        and execution["ordered_workload_ids"] == [slot.workload_id for slot in slots]
        and execution["max_concurrency"] == max(len(slot.arms) for slot in slots)
        and execution["timeout_seconds"] == AGENT_BUDGET
        and isinstance(execution["budget"].get("limit"), int)
        and execution["budget"]["limit"] > 0
        and primary["name"] == config["metric"]
        and primary["denominator"] == config["denominator"]
        and sha(ROOT / "runner.py") in spec["reproduction"]["harness"]["source"]
    ):
        raise ValueError(f"{unit}: run-spec differs from the frozen unit contract")


def bound_inputs(cells: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    paths = {ROOT / name for name in LOCAL_FILES} | {MANIFEST}
    paths |= {LEGACY_ROOT / name for name in PINS}
    for cell in cells:
        paths.add(Path(cell["case_file"]))
        paths.update(p for p in Path(cell["task_dir"]).rglob("*") if p.is_file())
    for path in paths:
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"frozen input must be a regular file: {path}")
    return {str(path): sha(path) for path in sorted(paths)}


def freeze(
    unit: str,
    *,
    run_spec: Path,
    bundle: Path,
    arm_c: bool,
    selection_freeze: Path | None,
    barrier: bool,
) -> dict[str, Any]:
    from evals.platforms.harbor_runtime import _verify_bundle
    from scripts.eval.contract import validate_run_spec

    if importlib.metadata.version("harbor") != "0.22.0":
        raise ValueError("wrong Harbor version")
    if source_pin.clean_revision(SOURCE) != REVISION:
        raise ValueError("pinned checkout moved")
    if arm_c != (selection_freeze is not None):
        raise ValueError("arm C needs its selection freeze, and only arm C uses one")
    if unit == "U0f" and not arm_c:
        raise ValueError("U0f is the arm C admission; it runs only with arm C approved")
    if arm_c and unit not in {"U0f", "U7r0", "U7r1"}:
        raise ValueError("arm C is pre-registered for U0f and U7 only")
    manifest = read(MANIFEST)
    if not (
        manifest["schema"] == "jev-v3.e2e-payload-manifest@1"
        and manifest["option"] == "E"
        and manifest["source_revision"] == REVISION
        and "@sha256:" in manifest["image_digest"]
        and manifest["oracle_sha256"]
        == sha(SOURCE / "evals/benchmarks/decision_handoff_runtime.py")
        and manifest["uv_lock_sha256"] == sha(SOURCE / "uv.lock")
        and manifest["slots_sha256"] == sha(SLOTS)
        and manifest["sources_sha256"] == sha(SOURCES)
        and unit in manifest["units"]
    ):
        raise ValueError("payload manifest does not match the pinned source, slots and sources")
    bundle = bundle.resolve(strict=True)
    _verify_bundle(bundle, sha(bundle))
    canonical = base.subprocess.check_output(
        ["git", "archive", "--format=tar.gz", REVISION, "--", *base_source_paths()], cwd=SOURCE
    )
    if hashlib.sha256(canonical).hexdigest() != sha(bundle):
        raise ValueError("source archive differs from committed bytes")
    with tarfile.open(bundle) as archive:
        if archive.pax_headers.get("comment") != REVISION:
            raise ValueError("archive lacks matching git commit provenance")
    tau = _selection_tau(selection_freeze) if selection_freeze is not None else None
    slots = unit_slots(unit, arm_c=arm_c)
    if any(slot.source in PREVIEW_SOURCES for slot in slots):
        raise ValueError(
            "preview or placeholder slot rows cannot be frozen; regenerate the matrix from e2e-sources.json"
        )
    width = max(len(slot.arms) for slot in slots)
    proof_path, _ = require_infrastructure(width)
    cells = build_cells(unit, slots, manifest, tau=tau, barrier=barrier)
    from evals.benchmarks.decision_metrics import policy_digest, reset_digest

    for cell in cells:
        _check_task(cell, manifest)
        cell["policy_digest"] = policy_digest(
            cell_policy(
                cell, task_checksum=cell["task_checksum"], verifier_sha256=cell["verifier_sha256"]
            )
        )
        cell["reset_digest"] = reset_digest(RESET_BOUNDARY)
    caps = derive_jev_call_caps(SOURCE)
    for cell in cells:
        cell["jev_call_cap"] = caps["judge_per_trial"] if cell["uses_jev"] else 0
    admission = _check_admission(unit, arm_c=arm_c)
    spec = validate_run_spec(run_spec)
    _check_spec(unit, spec, slots)
    directory = phase_dir(unit)
    directory.mkdir(mode=0o700)
    raw_spec = run_spec.read_bytes()
    with (directory / "run-spec.json").open("xb") as handle:
        handle.write(raw_spec)
    if validate_run_spec(directory / "run-spec.json") != spec:
        raise ValueError("run-spec copy changed")
    write(directory / "host-environment.json", base.host_environment())
    bound = bound_inputs(cells)
    bound.update(admission)
    for path in (
        bundle,
        directory / "run-spec.json",
        directory / "host-environment.json",
        proof_path,
    ):
        bound[str(path)] = sha(path)
    if selection_freeze is not None:
        bound[str(selection_freeze.resolve())] = sha(selection_freeze)
    planned_astra = int(spec["reproduction"]["execution"]["budget"]["limit"])
    record = {
        "schema": "jev-v3.e2e-freeze@1",
        "unit": unit,
        "phase": unit.lower(),
        "run_id": spec["run_id"],
        "frozen_at": now(),
        "source_revision": REVISION,
        "source_bundle": str(bundle),
        "source_sha256": sha(bundle),
        "harbor_version": "0.22.0",
        "image_digest": manifest["image_digest"],
        "infra_proof_at_freeze": {"path": proof_path.name, "sha256": sha(proof_path)},
        "arm_c": arm_c,
        "cascade_tau": tau,
        "barrier": barrier,
        "slot_width": width,
        "slots": [slot.slot_id for slot in slots],
        "cells": cells,
        "planned_astra_call_cap": planned_astra,
        "planned_jev_calls": sum(cell["uses_jev"] for cell in cells) * caps["judgments_per_trial"],
        "jev_call_caps": caps,
        "expected_account": {"fp12": EXPECTED_ACCOUNT_FP12, "plan": EXPECTED_PLAN},
        "limits": {
            "dispatch_skew_limit_s": 1.0,
            "agent_start_sync_limit_s": 30.0,
            "barrier_timeout_s": 120.0,
            "watchdog_s": WATCHDOG,
            "cleanup_s": CLEANUP,
            "quota_start_pct": 90.0,
            "quota_stop_pct": 95.0,
            "jev_calls_reserved_per_trial": caps["judge_per_trial"],
        },
        "reset_boundary": RESET_BOUNDARY,
        "sha256": bound,
    }
    write(directory / "freeze.json", record)
    print(f"{unit}: frozen {len(cells)} trials in {len(slots)} slots; no execution")
    return record


def base_source_paths() -> tuple[str, ...]:
    return (
        ".geode",
        "core",
        "evals",
        "evolve",
        "scripts",
        "pyproject.toml",
        "uv.lock",
        "GEODE.md",
        "README.md",
        "README.ko.md",
        "CHANGELOG.md",
        "LICENSE",
        "NOTICE",
    )


def preflight(unit: str) -> tuple[dict[str, Any], dict[str, Any], Path]:
    from harbor.models.task.task import Task
    from scripts.eval.contract import validate_run_spec

    directory = phase_dir(unit)
    frozen = read(directory / "freeze.json")
    spec = validate_run_spec(directory / "run-spec.json")
    if not (
        frozen["unit"] == unit
        and importlib.metadata.version("harbor") == frozen["harbor_version"] == "0.22.0"
        and source_pin.clean_revision(SOURCE) == frozen["source_revision"] == REVISION
        and spec["reproduction"]["geode"]["revision"] == REVISION
        and all(sha(Path(path)) == digest for path, digest in frozen["sha256"].items())
        and read(directory / "host-environment.json") == base.host_environment()
    ):
        raise ValueError(f"{unit}: frozen inputs, source or host environment changed")
    proof_path, _ = require_infrastructure(frozen["slot_width"])
    slots = unit_slots(unit, arm_c=frozen["arm_c"])
    expected = build_cells(
        unit, slots, read(MANIFEST), tau=frozen["cascade_tau"], barrier=frozen["barrier"]
    )
    if len(expected) != len(frozen["cells"]):
        raise ValueError(f"{unit}: frozen cell count changed")
    for actual, cell in zip(frozen["cells"], expected, strict=True):
        if any(actual[key] != value for key, value in cell.items()):
            raise ValueError(f"{unit}: frozen cell {cell['index']} changed")
        if Task(cell["task_dir"]).checksum != actual["task_checksum"]:
            raise ValueError(f"{unit}: task checksum changed")
    caps = derive_jev_call_caps(SOURCE)
    if any(
        cell.get("jev_call_cap") != (caps["judge_per_trial"] if cell["uses_jev"] else 0)
        for cell in frozen["cells"]
    ):
        raise ValueError(f"{unit}: frozen Jev call caps differ from the pinned source")
    _check_admission(unit, arm_c=frozen["arm_c"])
    return spec, frozen, proof_path


# --- child ----------------------------------------------------------------------


def trial_config(frozen: Mapping[str, Any], cell: Mapping[str, Any], secret: Path | None) -> Any:
    from harbor.models.trial.config import (
        AgentConfig,
        EnvironmentConfig,
        TaskConfig,
        TrialConfig,
        VerifierConfig,
    )

    kwargs: dict[str, Any] = {
        "source_bundle": frozen["source_bundle"],
        "source_sha256": frozen["source_sha256"],
        "source_revision": frozen["source_revision"],
        "provider": "openai",
        "source": "subscription",
        "effort": "xhigh",
        "verify_mode": "llm_judge",
        "agent_timeout_sec": ROOT_BUDGET,
        "arm": "a0",
        "case_file": cell["case_file"],
        "case_sha256": cell["case_sha256"],
        "verification_engine": cell["verification_engine"],
    }
    if cell["verification_primitive"] == "noul":
        kwargs["verification_primitive"] = "noul"
    if cell["cascade_tau"] is not None:
        kwargs["cascade_tau"] = cell["cascade_tau"]
    if secret is not None:
        kwargs["typesafe_key_file"] = str(secret)
    import_path = "evals.platforms.harbor_handoff:GeodeHandoffHarborAgent"
    if cell["barrier"]:
        peers = [c["arm_letter"] for c in frozen["cells"] if c["slot_id"] == cell["slot_id"]]
        import_path = "slot_agent:SlotBarrierHandoffAgent"
        kwargs.update(
            barrier_dir=str(barrier_dir(cell)),
            barrier_arm=cell["arm_letter"],
            barrier_peers=[peer for peer in peers if peer != cell["arm_letter"]],
            barrier_timeout_sec=120.0,
        )
    return TrialConfig(
        task=TaskConfig(path=Path(cell["task_dir"])),
        trial_name=cell["trial_name"],
        trials_dir=phase_dir(cell["unit"]) / "trials",
        agent=AgentConfig(
            import_path=import_path,
            model_name="gpt-6-astra",
            override_timeout_sec=AGENT_BUDGET,
            override_setup_timeout_sec=600,
            kwargs=kwargs,
        ),
        environment=EnvironmentConfig(
            import_path="runner:ObservedDockerEnvironment", delete=True, force_build=False
        ),
        verifier=VerifierConfig(override_timeout_sec=30, disable=False),
    )


def barrier_dir(cell: Mapping[str, Any]) -> Path:
    return phase_dir(cell["unit"]) / "slots" / cell["slot_id"] / "barrier"


async def child(unit: str, index: int, secret: Path | None) -> int:
    from harbor.trial.trial import Trial

    _, frozen, _ = preflight(unit)
    cell = frozen["cells"][index]
    if cell["uses_jev"] != (secret is not None):
        raise ValueError("secret arm mismatch")
    task = asyncio.current_task()
    assert task is not None
    asyncio.get_running_loop().add_signal_handler(signal.SIGTERM, task.cancel)
    trial = await Trial.create(trial_config(frozen, cell, secret))
    assert trial.agent_environment.session_id == cell["trial_name"] + "__env"
    try:
        await trial.run()
    finally:
        asyncio.get_running_loop().remove_signal_handler(signal.SIGTERM)
    return 0


# --- collection -------------------------------------------------------------------


QUOTA_ERRORS = ("Billing", "RateLimit", "Quota", "quota", "rate_limit", "UsageLimit")


def failure_class(row: Mapping[str, Any]) -> str | None:
    if row.get("valid"):
        return None if row.get("passed") else "semantic_failure"
    error = str(row.get("error_type") or row.get("collection_error_type") or "unknown")
    if any(marker in error for marker in QUOTA_ERRORS):
        return "quota_or_rate_limit"
    return error


def e2e_outcome(row: Mapping[str, Any], trial: Path, cell: Mapping[str, Any]) -> dict[str, Any]:
    """Strict success and recovery from retained receipts (05 v2 §3.1).

    Strict: native reward 1, every decisive judgment admitted, every negative
    judgment's feedback consumed by the next root request, no false completion.
    Recovery: the first decisive judgment is negative, a later root request consumes
    it, and the oracle passes.
    """
    outcome: dict[str, Any] = {
        "strict_success": None,
        "recovered": None,
        "first_judgment_negative": None,
        "all_judgments_admitted": None,
        "feedback_consumption_complete": None,
        "false_completion": None,
    }
    if not row.get("valid"):
        return outcome
    evidence = read(trial / "agent/verification.json")
    judgments = list(evidence.get("judgments") or [])
    if cell["verification_engine"] == "cascade":
        from evals.benchmarks.decision_cascade import decision_receipts

        judgments = decision_receipts(judgments)
    consumed = {
        item["judge_call_id"]
        for request in evidence.get("root_requests") or []
        for item in request.get("consumed_feedback") or []
    }
    negatives = [
        j
        for j in judgments[:-1]
        if j.get("accepted") and not (j.get("projected_payload") or {}).get("passed")
    ]
    reward = row.get("passed") is True
    native = (row.get("runtime") or {}).get("native_verify") or []
    final_pass = bool(native) and native[-1].get("action") == "turn.verify.passed"
    oracle_passed = ((row.get("independent_verifier") or {}).get("oracle") or {}).get("passed")
    first_negative = (
        bool(judgments)
        and judgments[0].get("accepted") is True
        and not (judgments[0].get("projected_payload") or {}).get("passed")
    )
    outcome.update(
        all_judgments_admitted=bool(judgments)
        and all(j.get("accepted") is True for j in judgments),
        feedback_consumption_complete=all(j.get("llm_call_id") in consumed for j in negatives),
        false_completion=bool(final_pass and oracle_passed is False),
        first_judgment_negative=first_negative,
    )
    outcome["strict_success"] = bool(
        reward
        and outcome["all_judgments_admitted"]
        and outcome["feedback_consumption_complete"]
        and not outcome["false_completion"]
    )
    outcome["recovered"] = bool(
        first_negative and judgments[0].get("llm_call_id") in consumed and reward
    )
    return outcome


def jev_calls_for(
    row: Mapping[str, Any], trial: Path, cell: Mapping[str, Any]
) -> list[dict[str, Any]]:
    """Observed Jev calls for settlement; unknown counts settle conservatively."""
    from evals.benchmarks.jev_cost_ledger import jev_calls_from_call_accounting

    if not cell["uses_jev"]:
        return []
    runtime = row.get("runtime")
    if isinstance(runtime, dict) and isinstance(runtime.get("call_accounting"), list):
        return jev_calls_from_call_accounting(runtime["call_accounting"])
    path = trial / "agent/call-events.json"
    if path.is_file():
        try:
            events = read(path)
            return jev_calls_from_call_accounting(
                [
                    {**event.get("payload", {}), "llm_attempt_id": event.get("llm_attempt_id")}
                    for event in events
                    if isinstance(event, dict) and event.get("action") == "llm.call.ended"
                ]
            )
        except (OSError, ValueError, TypeError):
            pass
    return [{"call_id": None, "input_tokens": None}] * int(cell["jev_call_cap"])


def collect_trial(
    unit: str, spec: Mapping[str, Any], frozen: Mapping[str, Any], cell: dict[str, Any], run: ArmRun
) -> dict[str, Any]:
    """r2 collection plus primitive, cascade tau, final-check and Noul scoring."""
    from scripts.eval.check_harbor_observations import validate_observations

    directory = phase_dir(unit)
    trial = directory / "trials" / cell["trial_name"]
    elapsed = (
        None
        if run.launched_at is None or run.exited_at is None
        else round(run.exited_at - run.launched_at, 3)
    )
    error = run.error or (None if run.exit_code in (0, None) else "child_nonzero")
    row: dict[str, Any] = {
        **cell,
        "valid": False,
        "passed": False,
        "error_type": error,
        "host_elapsed_seconds": elapsed,
        "actual_charge_usd": None,
    }
    try:
        native = read(trial / "result.json") if (trial / "result.json").is_file() else None
        row["agent_start_utc"], row["agent_end_utc"] = agent_interval(native)
        runtime_path = trial / "agent/handoff-result.json"
        if runtime_path.is_file():
            row["runtime"] = read(runtime_path)
            row["error_type"] = row["runtime"].get("error_type") or error
        elif (trial / "agent/runtime-result.json").is_file():
            metadata = read(trial / "agent/runtime-result.json").get("metadata", {})
            row["execution_started"] = metadata.get("execution_started")
            row["error_type"] = metadata.get("error_type") or error
        if not (row.get("runtime") or {}).get("valid"):
            row["error_type"] = row["error_type"] or "missing_or_invalid_runtime"
            base.audit_invalid_trial(row, trial, cell)
            return _finish(row, trial, cell)
        cleanup = base.cleanup_observation(cell, trial)
        write(trial / "cleanup-observation.json", cleanup)
        assert cleanup["complete"] and cleanup["verifier_identity_recorded"]
        assert native is not None
        finalized = read(trial / "agent/runtime-finalized.json")
        verifier = read(trial / "verifier/verifier-receipt.json")
        runtime = row["runtime"]
        row.update(
            native_reward=native["verifier_result"]["rewards"], independent_verifier=verifier
        )
        assert native["exception_info"] is None and error is None
        assert runtime["source_snapshot_complete"] is True
        assert runtime["verification_engine"] == cell["verification_engine"]
        assert runtime.get("verification_primitive", "choice") == cell["verification_primitive"]
        assert runtime.get("cascade_tau") == cell["cascade_tau"]
        assert finalized["exports_complete"] and not finalized["finalization_errors"]
        assert verifier["valid"] and verifier.get("error_type") is None
        source_db = trial / "agent" / Path(runtime["db_path"]).relative_to("/logs/agent")
        assert source_db.resolve().is_relative_to((trial / "agent").resolve())
        report = validate_observations(
            trial,
            run_spec_path=directory / "run-spec.json",
            run_spec_sha256=sha(directory / "run-spec.json"),
            source_sha256=frozen["source_sha256"],
            trial_name=cell["trial_name"],
            task_name=cell["task_name"],
            task_checksum=cell["task_checksum"],
            require_uniform_effort=False,
            handoff_arm="a0",
            handoff_case_sha256=cell["case_sha256"],
            source_db=source_db,
            expected_effective_verify_mode="llm_judge",
            verification_engine=cell["verification_engine"],
            verification_primitive=cell["verification_primitive"],
            cascade_tau=cell["cascade_tau"],
        )
        assert report["observation_valid"]
        write(trial / "observation-check.json", report)
        replay = base.replay_observation(trial)
        write(trial / "replay-check.json", replay)
        row["replay"] = replay
        rewards = native["verifier_result"]["rewards"]
        assert isinstance(rewards, dict) and len(rewards) == 1
        reward = next(iter(rewards.values()))
        assert type(reward) in (int, float) and reward in (0, 1)
        assert bool(reward) == verifier["passed"] == runtime["passed"]
        row.update(valid=True, passed=bool(reward), error_type=None)
    except Exception as exc:
        row["collection_error_type"] = type(exc).__name__
        row["error_type"] = row["error_type"] or type(exc).__name__
    return _finish(row, trial, cell)


def _finish(row: dict[str, Any], trial: Path, cell: Mapping[str, Any]) -> dict[str, Any]:
    row["validity"] = "valid" if row["valid"] else "invalid"
    row["outcome"] = ("passed" if row["passed"] else "failed") if row["valid"] else "unknown"
    row["failure_class"] = failure_class(row)
    try:
        row["e2e"] = e2e_outcome(row, trial, cell)
    except Exception as exc:
        row.update(valid=False, validity="invalid", outcome="unknown")
        row["failure_class"] = row["error_type"] = "metric_projection_" + type(exc).__name__
    if row["valid"] and cell["cell"] != "natural":
        from evals.benchmarks.noul_conditions import score_trial

        try:
            row["noul_score"] = score_trial(
                read(trial / "agent/verification.json"),
                read(Path(cell["case_file"])),
                primitive=cell["verification_primitive"],
            )
        except Exception as exc:
            row["noul_score"] = {"error_type": type(exc).__name__}
    barrier = barrier_dir(cell) / f"{cell['arm_letter']}.json"
    row["barrier_receipt"] = read(barrier) if cell["barrier"] and barrier.is_file() else None
    row["jev_calls"] = jev_calls_for(row, trial, cell)
    return row


# --- recording and analysis ----------------------------------------------------------


class UnitState:
    """Write each finished slot: trial receipts, attempts and private receipts."""

    def __init__(
        self,
        unit: str,
        spec: Mapping[str, Any],
        frozen: Mapping[str, Any],
        *,
        account: AccountGuard,
        jev: JevGuard,
        quota_start: Mapping[str, str],
        proof_path: Path,
    ) -> None:
        self.unit, self.spec, self.frozen = unit, spec, frozen
        self.account, self.jev, self.quota_start = account, jev, quota_start
        self.directory = phase_dir(unit)
        self.proof_sha256 = sha(proof_path)
        self.cells = {(c["slot_id"], c["arm_letter"]): c for c in frozen["cells"]}
        self.rows: list[dict[str, Any]] = []
        self.attempts: list[dict[str, Any]] = []
        self.refs: list[dict[str, str]] = []
        self.reports: list[SlotReport] = []

    def record(self, report: SlotReport) -> None:
        from scripts.eval.contract import validate_attempts

        self.reports.append(report)
        for arm in report.slot.launch_order:
            cell = self.cells[(report.slot.slot_id, arm)]
            run, row = report.runs[arm], report.rows[arm]
            for key, value in cell.items():  # dispatcher-made rows (prepare failure) lack the cell
                row.setdefault(key, value)
            row.setdefault("valid", False)
            row.setdefault("passed", False)
            trial = self.directory / "trials" / cell["trial_name"]
            trial.mkdir(parents=True, exist_ok=True, mode=0o700)
            row["concurrency"] = report.concurrency_fields(arm)
            row["semantic_metrics"] = semantic_metrics(row)
            write(trial / "trial-receipt.json", _jsonable(row))
            refs = base.evidence(self.directory, trial)
            # An arm refused at prepare never launched; its attempt is timed at the refusal record.
            started = run.host_launch_utc or now()
            attempt = {
                "schema_id": "geode.eval-attempt@1",
                "schema_version": 1,
                "run_id": self.spec["run_id"],
                "attempt_id": f"{self.spec['run_id']}-a{cell['index']:04d}",
                "parent_attempt_id": None,
                "sequence": len(self.attempts),
                "timing": {
                    "status": "exact",
                    "started_at": started,
                    "finished_at": run.host_exit_utc or started,
                    "source_ref": None,
                },
                "validity": row["validity"],
                "outcome": row["outcome"],
                "change": {
                    "surface": self.unit.lower(),
                    "description": f"{report.slot.slot_id} {cell['workload_id']} arm {arm} "
                    f"({cell['verification_engine']}); paired concurrent slot; no retry",
                },
                "expected_effect": self.spec["study"]["hypothesis"],
                "observed_result": "See the native verifier and private trial receipt; "
                "semantic outcome is separate from measurement validity.",
                "failure_class": row["failure_class"],
                "error_ref": None,
                "evidence_refs": refs,
                "selected_for_analysis": True,
            }
            append(self.directory / "attempts.jsonl", attempt)
            validate_attempts(self.directory / "attempts.jsonl")
            context = {
                "run_id": self.spec["run_id"],
                "unit": self.unit,
                "source_revision": REVISION,
                "harbor_version": self.frozen["harbor_version"],
                "image_digest": self.frozen["image_digest"],
                "infra_proof_sha256": self.proof_sha256,
                "host_environment_sha256": sha(self.directory / "host-environment.json"),
            }
            write_private_receipt(
                self.directory,
                private_receipt(
                    report,
                    arm,
                    cell=cell,
                    attempt=attempt,
                    context=context,
                    account=self.account,
                    jev=self.jev,
                    quota_start=self.quota_start,
                ),
            )
            self.rows.append(row)
            self.attempts.append(attempt)
            self.refs.extend(refs)
        append(self.directory / "slots.jsonl", report.summary())


def semantic_metrics(row: Mapping[str, Any]) -> dict[str, Any]:
    runtime = row.get("runtime") or {}
    oracle = (row.get("independent_verifier") or {}).get("oracle") or {}
    metrics = {
        key: oracle.get(key)
        for key in (
            "lookup_attempt_count",
            "lookup_item_count",
            "extra_lookup_count",
            "wrong_target_lookup_count",
            "rejected_lookup_count",
            "false_completion_count",
        )
    }
    metrics.update(runtime.get("verification_metrics") or {})
    native = runtime.get("native_verify") or []
    metrics["judge_false_acceptance"] = bool(
        native
        and native[-1].get("action") == "turn.verify.passed"
        and native[-1].get("success") is True
        and oracle.get("passed") is False
    )
    metrics["held_delivery"] = runtime.get("termination_reason") == "external_verification_required"
    metrics.update(row.get("e2e") or {})
    return metrics


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _jsonable(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False, default=str))


def primary_for(unit: str, rows: Sequence[Mapping[str, Any]], complete: bool) -> dict[str, Any]:
    config = UNITS[unit]
    denominator = config["denominator"]
    if not complete:
        return {"value": "not-measurable", "numerator": None, "denominator": None}
    if config["kind"] == "admission":
        numerator = sum(bool(r["valid"] and r["passed"]) for r in rows)
    else:
        key = "strict_success" if config["kind"] == "natural" else "recovered"
        slots: dict[str, dict[str, bool]] = {}
        for row in rows:
            slots.setdefault(row["slot_id"], {})[row["verification_engine"]] = bool(
                (row.get("e2e") or {}).get(key)
            )
        numerator = sum(
            int(arms.get("jev", False)) - int(arms.get("llm", False)) for arms in slots.values()
        )
    return {"value": numerator / denominator, "numerator": numerator, "denominator": denominator}


def reliability_for(
    unit: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    """Bind the two preregistered repeats only in U7r1's first analysis write."""
    if unit != "U7r1":
        return [], [], []
    from scripts.eval.denominator_coverage import check_repetition_matrix
    from scripts.eval.handoff_tables import export_reliability, reliability_metric_rows

    phases = [phase_dir("U7r0"), phase_dir("U7r1")]
    tables = phases[1] / "tables"
    gate = check_repetition_matrix(phases, primitive="choice", n=2)
    summary = export_reliability(phases, tables, primitive="choice", unit="u7", ns=(1, 2))
    write(tables / "reliability_gate.json", gate)
    metrics = reliability_metric_rows(summary)
    limitations = [
        "U7 reliability: 12 tasks, two full repeats; small-sample descriptive auxiliary."
    ]
    phases_complete = all(read(phase / "results.json").get("complete") is True for phase in phases)
    if not gate["covered"] or not phases_complete:
        # Preserve native arm-level diagnostics; the planned comparison as a whole
        # is not measurable when either phase has missing/invalid evidence (§3.7).
        metrics = [
            {
                **row,
                "value": "not-measurable",
                "numerator": None,
                "denominator": None,
                "source_locator": None,
            }
            for row in metrics
        ]
        limitations.append(
            "U7 planned repetition matrix incomplete; all reliability metrics withheld."
        )
    refs = [
        {"kind": "other", "path": f"tables/{name}", "sha256": sha(tables / name)}
        for name in ("reliability_summary.json", "reliability_gate.json")
    ]
    return metrics, refs, limitations


def analyze(
    unit: str,
    spec: Mapping[str, Any],
    frozen: Mapping[str, Any],
    state: UnitState,
    report: UnitReport,
) -> int:
    from evals.benchmarks.decision_handoff_runtime import _aggregate_accounting
    from scripts.eval.contract import validate_analysis

    directory = phase_dir(unit)
    rows = state.rows
    complete = (
        report.complete
        and len(rows) == len(frozen["cells"])
        and all(row["validity"] == "valid" for row in rows)
    )
    primary = primary_for(unit, rows, complete)
    arms: dict[str, Any] = {}
    for engine in sorted({row["verification_engine"] for row in rows}):
        selected = [row for row in rows if row["verification_engine"] == engine]
        calls = [c for r in selected for c in (r.get("runtime") or {}).get("call_accounting", [])]
        valid_times = [r["runtime"]["elapsed_seconds"] for r in selected if r["valid"]]
        arms[engine] = {
            "attempted": len(selected),
            "valid": sum(r["valid"] for r in selected),
            "passed": sum(bool(r["valid"] and r["passed"]) for r in selected),
            "strict_success": sum(
                bool((r.get("e2e") or {}).get("strict_success")) for r in selected
            ),
            "recovered": sum(bool((r.get("e2e") or {}).get("recovered")) for r in selected),
            "median_valid_runtime_seconds": statistics.median(valid_times) if valid_times else None,
            "accounting": _aggregate_accounting(calls, complete=complete),
        }
    pairs = []
    for slot_report in state.reports:
        by_engine = {row["verification_engine"]: row for row in slot_report.rows.values()}
        a, b = by_engine.get("llm"), by_engine.get("jev")
        paired = bool(a and b and a["valid"] and b["valid"])
        pairs.append(
            {
                "slot_id": slot_report.slot.slot_id,
                "workload_id": slot_report.slot.workload_id,
                "repetition": slot_report.slot.repetition,
                "pair_sync": slot_report.pair_sync,
                "dispatch_skew_s": slot_report.launch_skew_s,
                "agent_start_skew_s": slot_report.agent_start_skew_s,
                "strict_success_delta": int(bool(b["e2e"]["strict_success"]))
                - int(bool(a["e2e"]["strict_success"]))
                if paired
                else None,
                "recovery_delta": int(bool(b["e2e"]["recovered"]))
                - int(bool(a["e2e"]["recovered"]))
                if paired
                else None,
                "runtime_seconds_delta": b["runtime"]["elapsed_seconds"]
                - a["runtime"]["elapsed_seconds"]
                if paired and slot_report.pair_sync
                else None,
            }
        )
    result = {
        "unit": unit,
        "phase": unit.lower(),
        "run_id": spec["run_id"],
        "complete": complete,
        "planned_cells": len(frozen["cells"]),
        "observed_cells": len(rows),
        "primary": primary,
        "arms": arms,
        "pairs": pairs,
        "dispatch": report.summary(),
        "slots": [r.summary() for r in state.reports],
        "actual_charge_usd": None,
        "trials": [
            {
                k: r.get(k)
                for k in (
                    "trial_name",
                    "slot_id",
                    "verification_engine",
                    "validity",
                    "outcome",
                    "failure_class",
                )
            }
            for r in rows
        ],
        "limitations": [
            "Shared Codex account: external usage unknown; latency is interpreted within pairs only.",
            "pair_sync=false pairs are excluded from within-pair latency, kept for success and recovery.",
            "Actual charges unknown; Jev amounts are tariff estimates from the host ledger.",
        ],
    }
    write(directory / "results.json", result)
    ref = {
        "kind": "native-result",
        "path": "results.json",
        "sha256": sha(directory / "results.json"),
    }
    aggregate_id = spec["run_id"] + "-aggregate"
    answer = (
        "Complete diagnostic; paired concurrent slots; interpret with burden and consumption."
        if complete
        else "Stopped or incomplete; primary not measurable; every planned-cell outcome is preserved."
    )
    append(
        directory / "attempts.jsonl",
        {
            "schema_id": "geode.eval-attempt@1",
            "schema_version": 1,
            "run_id": spec["run_id"],
            "attempt_id": aggregate_id,
            "parent_attempt_id": state.attempts[-1]["attempt_id"] if state.attempts else None,
            "sequence": len(state.attempts),
            "timing": {
                "status": "exact",
                "started_at": now(),
                "finished_at": now(),
                "source_ref": None,
            },
            "validity": "valid" if complete else "invalid",
            "outcome": "mixed" if complete else "unknown",
            "change": {
                "surface": "analysis-only",
                "description": "Deterministic aggregate; zero model calls.",
            },
            "expected_effect": "Apply the frozen denominator",
            "observed_result": answer,
            "failure_class": None
            if complete
            else (report.stop.failure_class if report.stop else "incomplete_planned_cells"),
            "error_ref": None,
            "evidence_refs": [ref],
            "selected_for_analysis": True,
        },
    )
    reliability_metrics, reliability_refs, reliability_limits = reliability_for(unit)
    write(
        directory / "analysis.json",
        {
            "schema_id": "geode.eval-analysis@1",
            "schema_version": 1,
            "run_id": spec["run_id"],
            "analyzed_at": now(),
            "run_spec_sha256": sha(directory / "run-spec.json"),
            "attempts_sha256": sha(directory / "attempts.jsonl"),
            "selected_attempt_ids": [a["attempt_id"] for a in state.attempts] + [aggregate_id],
            "answer": answer,
            "metrics": [
                {
                    "name": spec["study"]["primary_metric"]["name"],
                    **primary,
                    "unit": "ratio",
                    "source_ref": "results.json",
                    "source_locator": {
                        "value": "/primary/value",
                        "numerator": "/primary/numerator",
                        "denominator": "/primary/denominator",
                    }
                    if complete
                    else None,
                },
                *reliability_metrics,
            ],
            "decision": {
                "outcome": "diagnostic-only",
                "hypothesis_status": (
                    "supported"
                    if primary["numerator"] == UNITS[unit]["denominator"]
                    else "not-supported"
                )
                if complete and UNITS[unit]["kind"] == "admission"
                else "mixed"
                if complete
                else "invalidated",
                "rationale": "05 v2 §3.4: admission units pass or fail; U7 and U8 are descriptive.",
            },
            "limitations": [*result["limitations"], *reliability_limits],
            "evidence_refs": [*state.refs, ref, *reliability_refs],
        },
    )
    validate_analysis(
        directory / "analysis.json",
        run_spec_path=directory / "run-spec.json",
        attempts_path=directory / "attempts.jsonl",
    )
    return 0 if complete else 1


def stop_unit(directory: Path, failure: str, reason: str, **extra: Any) -> None:
    directory.mkdir(mode=0o700, exist_ok=True)
    record = {"failure_class": failure, "reason": reason, "at": now(), **extra}
    write(directory / f"unit-stop-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.json", record)
    print(json.dumps({"unit_stopped": failure, "reason": reason}))


async def execute(unit: str, *, quota_live: bool) -> int:
    from evals.benchmarks.jev_cost_ledger import (
        JevBudgetRefusedError,
        JevCostLedger,
        JevLedgerError,
    )

    spec, frozen, proof_path = preflight(unit)
    directory = phase_dir(unit)
    run_id = spec["run_id"]
    lock = ExecutionLock(RUN_ROOT, mode="e2e-slot", run_id=run_id)
    try:
        lock.acquire()
    except ScheduleOverlapError as error:
        stop_unit(directory, "schedule_overlap", str(error), holder=error.holder)
        return 3
    try:
        slots = unit_slots(unit, arm_c=frozen["arm_c"])
        try:
            claims = account_fields(read_account_claims(codex_auth_file()), now=time.time())
        except (OSError, ValueError) as error:
            stop_unit(directory, "account_unreadable", type(error).__name__)
            return 3
        required = int(len(slots) * (WATCHDOG + CLEANUP) + AUTH_MARGIN_SLACK_S)
        refusal = account_refusal(claims, required_margin_s=required)
        if refusal:
            stop_unit(directory, refusal, "account guard refused the unit")
            return 3
        try:
            quota = QuotaLedger(QUOTA_LEDGER)
        except (OSError, ValueError) as error:
            stop_unit(directory, "quota_ledger_unavailable", type(error).__name__)
            return 3
        reader = live_snapshot if quota_live else None
        snapshot = (
            live_snapshot() if quota_live else latest_snapshot(quota, max_age_s=SNAPSHOT_MAX_AGE_S)
        )
        start = quota.start_decision(
            unit=unit,
            planned_astra_calls=frozen["planned_astra_call_cap"],
            snapshot=snapshot,
            account=claims,
            checkpoint_id=f"{unit}-start",
        )
        if start["decision"] not in ("start", "calibrating"):
            stop_unit(directory, "quota_" + start["decision"].replace("-", "_"), start["notes"])
            return 3
        try:
            ledger = JevCostLedger.open(JEV_LEDGER)
            ledger.admit_unit(run_id, frozen["planned_jev_calls"])
        except JevBudgetRefusedError as error:
            stop_unit(directory, "jev_budget_refused", error.reason)
            return 3
        except (OSError, ValueError, JevLedgerError) as error:
            stop_unit(directory, "jev_ledger_unavailable", type(error).__name__)
            return 3
        write(
            directory / "dispatch-lock.json",
            {
                "started_at": now(),
                "freeze_sha256": sha(directory / "freeze.json"),
                "infra_proof": {"path": proof_path.name, "sha256": sha(proof_path)},
                "quota_start": start,
                "account_fp12": claims["codex_account_fp12"],
            },
        )
        cells = {(c["slot_id"], c["arm_letter"]): c for c in frozen["cells"]}
        account = AccountGuard(
            claims,
            slots,
            reader=lambda: read_account_claims(codex_auth_file()),
            slot_bound_s=WATCHDOG + CLEANUP,
        )
        jev = JevGuard(ledger, run_id, cells)
        state = UnitState(
            unit, spec, frozen, account=account, jev=jev, quota_start=start, proof_path=proof_path
        )
        guards = [
            LockGuard(lock),
            StopFileGuard(directory),
            PreflightGuard(lambda: preflight(unit)),
            account,
            QuotaGuard(quota, unit, slots, frozen["planned_astra_call_cap"], reader),
            jev,
        ]

        async def collect(slot: Slot, run: ArmRun) -> dict[str, Any]:
            cell = cells[(slot.slot_id, run.arm)]
            try:
                return await asyncio.to_thread(collect_trial, unit, spec, frozen, dict(cell), run)
            except Exception as error:
                # Last resort: the slot is still recorded, guarded and settled (unknown Jev calls).
                failure = "collection_" + type(error).__name__
                return {
                    **cell,
                    "valid": False,
                    "passed": False,
                    "validity": "invalid",
                    "outcome": "unknown",
                    "failure_class": failure,
                    "error_type": failure,
                    "jev_calls": [{"call_id": None, "input_tokens": None}]
                    * int(cell["jev_call_cap"])
                    if cell["uses_jev"]
                    else [],
                }

        dispatcher = PairedDispatcher(
            driver=SubprocessDriver(
                cells=cells,
                runner=ROOT / "runner.py",
                mode_args=["--unit", unit],
                directory=directory,
                pythonpath=SOURCE,
                key_file=base.key_file,
                barrier_dir=barrier_dir,
                cleanup_s=CLEANUP,
            ),
            collect=collect,
            guards=guards,
            on_slot=state.record,
            watchdog_s=WATCHDOG,
            barrier_used=frozen["barrier"],
        )
        report = await dispatcher.run(slots)
        code = analyze(unit, spec, frozen, state, report)
        astra = [
            c
            for r in state.rows
            for c in (r.get("runtime") or {}).get("call_accounting", [])
            if c.get("model") == "gpt-6-astra"
        ]
        quota.end_record(
            unit=unit,
            snapshot=live_snapshot() if quota_live else None,
            start_used_pct=_float_or_none(start.get("used_pct")),
            unit_astra_calls=len(astra),
            unit_astra_input_tokens=sum(
                int((c.get("usage") or {}).get("input_tokens") or 0) for c in astra
            ),
            account=claims,
            checkpoint_id=f"{unit}-end",
        )
        print(
            json.dumps(
                {
                    "unit": unit,
                    **report.summary(),
                    "primary": read(directory / "results.json")["primary"],
                }
            )
        )
        return code
    finally:
        lock.release()


def main() -> int:
    if not __debug__:
        raise RuntimeError("Do not disable preparation checks")
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--infra-preflight", action="store_true")
    mode.add_argument("--quota-snapshot", action="store_true")
    mode.add_argument("--freeze", action="store_true")
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--child", type=int, help=argparse.SUPPRESS)
    parser.add_argument("--unit", choices=sorted(UNITS))
    parser.add_argument("--reviewed", action="store_true")
    parser.add_argument("--run-spec", type=Path)
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--arm-c", action="store_true")
    parser.add_argument("--selection-freeze", type=Path)
    parser.add_argument("--barrier", action="store_true")
    parser.add_argument("--concurrency", type=int, default=2)
    parser.add_argument("--quota-live", action="store_true", help="user-approved WHAM lookup")
    parser.add_argument("--used-pct", type=float)
    parser.add_argument("--window-seconds", type=int)
    parser.add_argument("--reset-at-kst")
    parser.add_argument("--checkpoint")
    parser.add_argument("--secret-file", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    ROOT.chmod(0o700)
    base.logging.disable(base.logging.CRITICAL)
    if args.self_test:
        import self_test

        return self_test.run()
    if args.infra_preflight:
        if not args.reviewed:
            parser.error("--infra-preflight requires --reviewed")
        asyncio.run(infrastructure(args.concurrency))
        return 0
    if args.quota_snapshot:
        if args.used_pct is None or not args.checkpoint:
            parser.error("--quota-snapshot needs --used-pct and --checkpoint")
        fields = account_fields(read_account_claims(codex_auth_file()), now=time.time())
        record_snapshot(
            QuotaLedger(QUOTA_LEDGER),
            QuotaSnapshot(args.used_pct, args.window_seconds, args.reset_at_kst, "operator-status"),
            account=fields,
            checkpoint_id=args.checkpoint,
        )
        return 0
    if not args.unit:
        parser.error("--unit is required")
    if args.freeze:
        if not (args.reviewed and args.run_spec and args.bundle):
            parser.error("--freeze needs --run-spec, --bundle and --reviewed")
        freeze(
            args.unit,
            run_spec=args.run_spec,
            bundle=args.bundle,
            arm_c=args.arm_c,
            selection_freeze=args.selection_freeze,
            barrier=args.barrier,
        )
        return 0
    if args.preflight:
        preflight(args.unit)
        print(f"{args.unit}: frozen input checks passed; no credential read")
        return 0
    if args.child is not None:
        return asyncio.run(child(args.unit, args.child, args.secret_file))
    if not args.reviewed:
        parser.error("--execute requires --reviewed")
    return asyncio.run(execute(args.unit, quota_live=args.quota_live))


if __name__ == "__main__":
    raise SystemExit(main())
