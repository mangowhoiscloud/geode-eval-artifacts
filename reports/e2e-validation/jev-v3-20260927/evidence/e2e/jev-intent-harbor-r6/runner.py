"""Two-helper Harbor diagnostic; live dispatch requires a reviewed frozen phase."""

from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import importlib
import importlib.metadata
import importlib.util
import inspect
import json
import math
import os
import re
import shlex
import statistics
import subprocess
import sys
import tarfile
import tempfile
from collections import Counter
from datetime import UTC, datetime, timedelta
from functools import partial
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parent
# The fixed source checkout and SHA come from this run folder's one-time pin:
# `--pin-source` writes it; every other mode and each dispatched child reads it.
PIN_FILE = ROOT / "source-pin.json"
PIN_SCHEMA = "geode.jev-runner-source-pin@1"
PIN_KEYS = {"schema", "source", "revision", "created_at"}
GIT = "/usr/bin/git"
LEGACY_ROOT = Path("withheld-local-path-f40f68724bf591b3")
PINS = {
    "runner.py": "2c1b1427e7634cadd2969464fd532915bdbcbec20e3840d1e538a813e69f1f40",
    "make_tasks.py": "2efc952c9723392455a92b6562f2a45f5d67aa1019fae0958ce6440e9658869d",
}
MANIFEST = ROOT / "task-bundle/manifest.json"
SOURCE_PATHS = (
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


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(checkout: Path, *args: str) -> str:
    return subprocess.run(  # noqa: S603 — fixed executable and arguments, no shell.
        [GIT, "-C", str(checkout), *args], check=True, capture_output=True, text=True
    ).stdout


def pin_source(source: Path, revision: str) -> None:
    """Record this run folder's clean fixed-SHA checkout exactly once; never overwrite."""
    if re.fullmatch(r"[0-9a-f]{40}", revision) is None:
        raise SystemExit("--revision must be a 40-character lowercase commit SHA")
    try:
        checkout = source.resolve(strict=True)
        toplevel = Path(git(checkout, "rev-parse", "--show-toplevel").strip()).resolve()
        head = git(checkout, "rev-parse", "HEAD").strip()
        dirty = git(checkout, "status", "--porcelain")
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
        descriptor = os.open(PIN_FILE, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        raise SystemExit(f"{PIN_FILE} exists; a run folder is pinned exactly once") from None
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(pin, indent=2) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    print(f"Pinned {revision} at {checkout}; no archive, Docker, credential or model access")


def load_source_pin() -> tuple[Path, str]:
    """Fail closed unless this run folder carries one well-formed source pin."""
    if PIN_FILE.is_symlink() or not PIN_FILE.is_file():
        raise SystemExit(
            f"source pin missing: {PIN_FILE}; first run: runner.py --pin-source "
            "--source <clean checkout> --revision <40-hex SHA>"
        )
    try:
        pin = json.loads(PIN_FILE.read_text(encoding="utf-8"))
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
        raise SystemExit(f"source pin malformed: {PIN_FILE}")
    source = Path(pin["source"])
    if not source.is_dir() or source.resolve() != source:
        raise SystemExit(f"pinned source checkout missing or not canonical: {source}")
    return source, pin["revision"]


if __name__ == "__main__" and "--pin-source" in sys.argv[1:]:
    # Handled before the import-time source work below, which needs the pin.
    _pin_parser = argparse.ArgumentParser(description="Write this run folder's source pin once.")
    _pin_parser.add_argument("--pin-source", action="store_true", required=True)
    _pin_parser.add_argument("--source", type=Path, required=True)
    _pin_parser.add_argument("--revision", required=True)
    _pin_arguments = _pin_parser.parse_args()
    os.umask(0o077)
    ROOT.chmod(0o700)
    pin_source(_pin_arguments.source, _pin_arguments.revision)
    raise SystemExit(0)

SOURCE, REVISION = load_source_pin()
FIXTURE = SOURCE / "evals/benchmarks/fixtures/decision-handoff-inbox.json"


def load_pinned(name: str):
    path = LEGACY_ROOT / name
    if sha(path) != PINS[name]:
        raise ValueError("reused orchestration source changed: " + name)
    spec = importlib.util.spec_from_file_location("intent_" + path.stem, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sys.path.insert(0, str(SOURCE))
importlib.import_module("evals.platforms.harbor_docker")
base = load_pinned("runner.py")
sys.path.remove(str(base.SOURCE))
base.ROOT, base.SOURCE, base.FIXTURE, base.MANIFEST = ROOT, SOURCE, FIXTURE, MANIFEST
base.ARMS = ("a", "b")
ObservedDockerEnvironment = base.ObservedDockerEnvironment
writer = load_pinned("make_tasks.py")
writer.ROOT, writer.SOURCE = ROOT, SOURCE
read, write = base.read, base.write
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# Paired E-track slots (05 v2 §2.4-§2.6): the same dispatcher, guards and receipt
# builder as the verdict E2E runner; these files are byte-identical copies.
from paired_dispatch import (  # noqa: E402
    PairedDispatcher,
    Slot,
    SubprocessDriver,
    agent_interval,
    load_slots,
    prebuild_images,
)
from run_guards import (  # noqa: E402
    AUTH_MARGIN_SLACK_S,
    ExecutionLock,
    QuotaLedger,
    ScheduleOverlapError,
    account_fields,
    account_refusal,
    codex_auth_file,
    derive_jev_call_caps,
    latest_snapshot,
    live_snapshot,
    read_account_claims,
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

RUN_ROOT = ROOT.parent
SLOTS = ROOT / "e2e-slots.jsonl"
UNIT_FOR_PHASE = {"admission": "U0c", "natural": "U6b"}
RUN_ID_NAME = {"admission": "choice-intent-admission", "natural": "choice-intent-natural"}
QUOTA_LEDGER = RUN_ROOT / "quota-ledger.csv"
JEV_LEDGER = RUN_ROOT / "jev-cost-ledger.jsonl"
# New recovery condition: one shared root clock for initial + two verification repairs.
ROOT_BUDGET_S = 540
AGENT_TIMEOUT_S = ROOT_BUDGET_S + 30
# Preserve the legacy outer allowance (930 - 210); this is not an empirical SLO.
WATCHDOG = float(AGENT_TIMEOUT_S + 720)
CLEANUP, SNAPSHOT_MAX_AGE_S = 120.0, 3600.0
_legacy_trial_config = base.trial_config


def trial_config(phase: str, frozen: dict, cell: dict, secret: Path | None):
    """Change only the two execution bounds at the legacy child's composition point."""
    config = _legacy_trial_config(phase, frozen, cell, secret)
    config.agent.kwargs["agent_timeout_sec"] = ROOT_BUDGET_S
    config.agent.override_timeout_sec = AGENT_TIMEOUT_S
    return config


# base.child resolves this module-global function at Trial.create; the pinned file stays intact.
base.trial_config = trial_config
base.WATCHDOG = WATCHDOG
SHARED_FILES = ("paired_dispatch.py", "run_guards.py", "slot_guards.py", "e2e-slots.jsonl")
# The helper route per arm: (provider, model) of the route that must answer analyze_request.
HELPER_ROUTE = {"a": ("openai", "gpt-6-astra"), "b": ("typesafe", "jev-1.13.0")}
HELPER_FIELDS = ("helper_admitted", "helper_fallback_used", "helper_feedback_consumed")
RESET_BOUNDARY = {
    "session": "fresh GEODE_HOME and session store inside a new agent container per trial",
    "files": "new public-network agent container and a separate no-network verifier per trial; "
    "no operator workspace mount; task files only from the frozen bundle",
    "cache": "no local cache shared across trials; provider-side prompt caching is not "
    "controlled and stays unknown",
}


def require_source() -> str:
    if base.clean_revision() != REVISION or importlib.metadata.version("harbor") != "0.22.0":
        raise ValueError("source or Harbor revision changed")
    for module_name, module in tuple(sys.modules.items()):
        path = getattr(module, "__file__", None)
        if (
            module_name.split(".")[0] in {"core", "evals", "scripts"}
            and path
            and not Path(path).resolve().is_relative_to(SOURCE)
        ):
            raise ValueError("import escaped the selected source checkout")
    for name, digest in PINS.items():
        assert sha(LEGACY_ROOT / name) == digest
    return REVISION


SCHEDULE_KEYS = (
    "index",
    "case_id",
    "arm",
    "intent_target_engine",
    "repetition",
    "position",
    "task_dir",
    "case_file",
    "trial_name",
    "task_name",
    "task_checksum",
    "case_sha256",
)


def schedule(phase: str, manifest: dict) -> list[dict]:
    entries = [manifest["admission"]] if phase == "admission" else manifest["cases"]
    cells = []
    for index, entry in enumerate(entries):
        for position, arm in enumerate(("a", "b") if index % 2 == 0 else ("b", "a")):
            cells.append(
                {
                    "index": len(cells),
                    "case_id": entry["case_id"],
                    "arm": arm,
                    "intent_target_engine": "llm" if arm == "a" else "jev",
                    "repetition": 0,
                    "position": position,
                    "task_dir": entry["task_dir"],
                    "case_file": entry["case_file"],
                    "trial_name": f"inbox-{phase}-r0-{entry['case_id']}-{arm}",
                }
            )
    assert len(cells) == (2 if phase == "admission" else 6)
    return cells


def proposed_spec(phase: str, cells: list[dict]) -> dict:
    spec = base.spec_for(phase, REVISION, cells, sha(MANIFEST))
    spec["run_id"] = f"geode-jev-{RUN_ID_NAME[phase]}-{datetime.now(UTC):%Y%m%d}-r6"
    spec["preregistration"].update(
        status="draft",
        frozen_at=None,
        live_test_approved=False,
        operator="Parent source/spec review pending; preparation only",
    )
    spec["study"].update(
        research_question=(
            "Does replacing a typed Astra intent-and-target helper with Jev preserve verified "
            "whole-inbox completion and change end-to-end burden?"
        ),
        hypothesis=(
            "Jev may reduce helper latency while whole-task success and total burden "
            "depend on the unchanged Astra consumer."
        ),
        decision_rule=(
            "Diagnostic only. Freeze after parent review; then both fresh admission arms "
            "and playback must pass before natural execution. No adoption or release authority."
        ),
        analysis_plan=(
            "Three author-visible inboxes, 12 items each, A/B once; 36 items and 72 intended "
            "Choice answers per arm. Distinguish intent, target, full task success, wrong/extra "
            "reads, false completion, rejudgments and per-purpose costs. Preselected replay: "
            "inbox-korean, repetition0. Final/cognitive/root Astra subscription xhigh remain "
            "common; raw rule_based alias resolves to effective llm_judge. "
            "No pooling with historical runs."
        ),
    )
    spec["study"]["primary_metric"] = {
        "name": "admission_success" if phase == "admission" else "strict_task_success_delta",
        "unit": "ratio",
        "direction": "target",
        "denominator": 2 if phase == "admission" else 3,
        "aggregation": "Verified passing admission arms / 2"
        if phase == "admission"
        else (
            "(B strict inbox passes - A strict inbox passes) / 3. Strict: native/oracle pass "
            "with consumed evidence and zero wrong-target/extra lookups or false completions."
        ),
    }
    reproduction = spec["reproduction"]
    reproduction["geode"]["branch"] = "codex/jev-intent-harbor-20260924"
    reproduction["execution"].update(
        max_concurrency=2,
        timeout_seconds=AGENT_TIMEOUT_S,
        budget={"kind": "combined", "limit": 13 if phase == "admission" else 75, "unit": "astra-xhigh-calls"},
        repetitions=1,
        seed_schedule=["unseeded-provider-inference-repeat-0"],
        command_redacted=(
            f"harbor-runner-022/bin/python -B runner.py --phase {phase} --execute --reviewed"
        ),
    )
    reproduction["comparison"]["comparator"] = (
        "A typed Astra intent+target helper versus B direct Jev1.13.0 helper; "
        "root/cognitive/final Astra subscription xhigh fixed"
    )
    return spec


def prepare() -> None:
    from evals.benchmarks.decision_handoff_runtime import inbox_request, validate_inbox_case
    from evals.platforms.harbor_runtime import _verify_bundle
    from harbor.models.task.task import Task

    require_source()
    cohort = read(FIXTURE)
    requirements = writer.requirements()
    entries = []
    for raw in [cohort["admission"], *cohort["cases"]]:
        case = {**raw, "profile": "inbox", "request": inbox_request(raw["items"])}
        validate_inbox_case(case, cohort["orders"])
        entries.append(writer.make(case, cohort["orders"], requirements))
    writer.write(
        MANIFEST,
        {
            "image_digest": writer.IMAGE,
            "fixture_sha256": sha(FIXTURE),
            "oracle_sha256": sha(SOURCE / "evals/benchmarks/decision_handoff_runtime.py"),
            "uv_lock_sha256": sha(SOURCE / "uv.lock"),
            "verifier_requirements_sha256": hashlib.sha256(requirements.encode()).hexdigest(),
            "cases": entries[1:],
            "admission": entries[0],
            "authority": (
                "Author-visible synthetic intent+target diagnostic; "
                "no mutations or leaderboard claim"
            ),
        },
    )
    archive = ROOT / "source.tar.gz"
    with archive.open("xb") as output:
        subprocess.run(  # noqa: S603 — fixed executable/revision/path allowlist, no shell.
            ["/usr/bin/git", "archive", "--format=tar.gz", REVISION, "--", *SOURCE_PATHS],
            cwd=SOURCE,
            stdout=output,
            check=True,
        )
    _verify_bundle(archive, sha(archive))
    with tarfile.open(archive) as bundle:
        assert bundle.pax_headers.get("comment") == REVISION
    manifest = read(MANIFEST)
    for phase in ("admission", "natural"):
        directory = ROOT / phase
        directory.mkdir(mode=0o700)
        cells = schedule(phase, manifest)
        for cell in cells:
            task = Task(cell["task_dir"])
            cell.update(
                task_name=task.name,
                task_checksum=task.checksum,
                case_sha256=sha(Path(cell["case_file"])),
            )
        write(directory / "schedule.proposed.json", cells)
        write(directory / "run-spec.proposed.json", proposed_spec(phase, cells))
    write(
        ROOT / "source-proof.json",
        {
            "stage": "prepared-not-frozen",
            "model_dispatches": 0,
            "revision": require_source(),
            "source_archive_sha256": sha(archive),
            "source_archive": str(archive),
            "fixture_sha256": sha(FIXTURE),
            "task_manifest_sha256": sha(MANIFEST),
            "reused_sources": PINS,
            "runner_sha256": sha(Path(__file__)),
            "protocol_sha256": sha(ROOT / "protocol.md"),
        },
    )
    print(
        "Prepared 2 admission + 6 natural cells, source archive and draft specs; "
        "no freeze or inference"
    )


def self_check() -> None:
    from core.agent.verify import VerifyMode, resolve_verify_mode
    from evals.benchmarks.decision_handoff import DecisionHandoffTool, order_mentions
    from evals.benchmarks.decision_handoff_runtime import verify_handoff_result
    from harbor.models.task.task import Task
    from jsonschema import Draft202012Validator

    require_source()
    checks = []
    manifest = read(MANIFEST)
    for phase in ("admission", "natural"):
        cells = read(ROOT / phase / "schedule.proposed.json")
        assert [(c["case_id"], c["arm"]) for c in cells] == [
            (c["case_id"], c["arm"]) for c in schedule(phase, manifest)
        ]
        spec = read(ROOT / phase / "run-spec.proposed.json")
        assert spec["preregistration"]["live_test_approved"] is False
        candidate = copy.deepcopy(spec)
        candidate["preregistration"].update(status="frozen", frozen_at=base.now())
        Draft202012Validator(read(SOURCE / "docs/eval/schemas/run-spec.schema.json")).validate(
            candidate
        )
        for cell in cells:
            task = Task(cell["task_dir"])
            assert task.checksum == cell["task_checksum"]
            payload = read(Path(cell["case_file"]))
            case = payload["case"]
            helper = DecisionHandoffTool(
                case["request"],
                "a",
                requests={item["id"]: item["request"] for item in case["items"]},
            )
            assert len(helper._payload()["questions"]) == 2 * len(case["items"])
            decisions = [
                {
                    "id": item["id"],
                    "intent": item["expected_intent"],
                    "source_sha256": hashlib.sha256(item["request"].encode()).hexdigest(),
                    "target": next(
                        (
                            value
                            for value in order_mentions(item["request"]).values()
                            if value["order_id"] == item["expected_order"]
                        ),
                        None,
                    ),
                }
                for item in case["items"]
            ]
            lookups = [
                {
                    "id": item["id"],
                    "order_id": item["expected_order"],
                    "status": item["expected_answer"]["status"],
                }
                for item in case["items"]
                if item["expected_answer"]["disposition"] == "answered"
            ]
            rows = [
                {
                    "kind": "tool_result",
                    "tool": "analyze_request",
                    "tool_call_id": "helper",
                    "result": {"result": {"items": decisions}},
                },
                {"kind": "root_request", "tool_result_ids": ["helper"]},
                {
                    "kind": "tool_result",
                    "tool": "lookup_order_status",
                    "tool_call_id": "lookup",
                    "result": {"result": {"items": lookups}},
                },
                {"kind": "root_request", "tool_result_ids": ["helper", "lookup"]},
            ]
            result = {
                "arm": cell["arm"],
                "final_text": json.dumps(
                    {
                        "items": [
                            {"id": item["id"], **item["expected_answer"]} for item in case["items"]
                        ]
                    }
                ),
                "tool_calls": [{"name": "analyze_request"}, {"name": "lookup_order_status"}],
            }
            oracle = verify_handoff_result(case, result, rows)
            assert oracle["passed"] is True and oracle["component_matches"] is True
            assert all(
                oracle[key] == 0
                for key in (
                    "wrong_target_lookup_count",
                    "extra_lookup_count",
                    "false_completion_count",
                )
            )
            missing_consumption = copy.deepcopy(rows)
            missing_consumption[-1]["tool_result_ids"] = ["helper"]
            assert verify_handoff_result(case, result, missing_consumption)["passed"] is False
            wrong_answer = {**result, "final_text": '{"items": []}'}
            assert verify_handoff_result(case, wrong_answer, rows)["passed"] is False
            extra_read = copy.deepcopy(rows)
            extra_read[2]["result"]["result"]["items"].append(copy.deepcopy(lookups[0]))
            extra_oracle = verify_handoff_result(case, result, extra_read)
            assert extra_oracle["passed"] is True and extra_oracle["extra_lookup_count"] == 1
            checks.append(
                {
                    "trial": cell["trial_name"],
                    "oracle_positive": True,
                    "missing_consumption_rejected": True,
                    "wrong_answer_rejected": True,
                    "canonical_pass_can_include_extra_lookup": True,
                }
            )
    assert resolve_verify_mode("rule_based") is VerifyMode.LLM_JUDGE
    write(
        ROOT / "offline-check.json",
        {
            "model_dispatches": 0,
            "synthetic_oracle_checks_not_rollouts": checks,
            "proposed_schema_valid_after_freeze_fields": True,
            "raw_verify_mode": "rule_based",
            "effective_verify_mode": "llm_judge",
            "runner_sha256": sha(Path(__file__)),
            "source_revision": require_source(),
        },
    )
    print(
        "8 proposed cells checked; positive, missing-consumption, wrong-answer and extra-lookup "
        "cases; no model calls"
    )


async def infrastructure() -> None:
    """Prebuild every task image, then two agent/verifier pairs at once; no model."""
    from harbor.environments.factory import EnvironmentFactory
    from harbor.models.task.task import Task
    from harbor.models.trial.config import EnvironmentConfig
    from harbor.models.trial.paths import TrialPaths

    require_source()
    directory = ROOT / "infrastructure"
    directory.mkdir(mode=0o700)
    manifest = read(MANIFEST)
    task = Task(manifest["admission"]["task_dir"])
    environments, observations, error, prebuilt = [], [], None, []

    async def pair(index: int) -> None:
        paths = TrialPaths(trial_dir=directory / f"native-{index}")
        paths.mkdir()
        for role, config, location in (
            ("agent", task.config.environment, task.paths.environment_dir),
            ("verifier", task.config.verifier.environment, task.paths.tests_dir),
        ):
            policy = config.resolve_baseline()
            environment = EnvironmentFactory.create_environment_from_config(
                config=EnvironmentConfig(
                    import_path="runner:ObservedDockerEnvironment", delete=True
                ),
                environment_dir=location,
                environment_name=task.short_name,
                session_id=f"jev-intent-harbor-infrastructure-{index}-{role}",
                trial_paths=paths,
                task_env_config=config,
                mounts=[],
                network_policy=policy,
                phase_network_policies=[policy],
            )
            environments.append(environment)
            await asyncio.wait_for(environment.start(force_build=False), timeout=600)
            output = await environment.exec(
                command="python -c " + shlex.quote(base.NETWORK_SCRIPT), timeout_sec=20
            )
            assert output.return_code == 0
            checked = base.inspect_network(json.loads(output.stdout), offline=role == "verifier")
            observations.append(
                {
                    "pair": index,
                    "role": role,
                    "session_id": environment.session_id,
                    "network": checked,
                }
            )
            if role == "verifier":
                probe = (
                    "import errno,socket\ns=socket.socket();s.settimeout(2)\n"
                    "try:s.connect(('192.0.2.1',443))\n"
                    "except OSError as e:assert e.errno==errno.ENETUNREACH\n"
                    "else:raise AssertionError('egress allowed')\nfinally:s.close()"
                )
                denied = await environment.exec(
                    command="python -c " + shlex.quote(probe), timeout_sec=10
                )
                assert denied.return_code == 0
                observations[-1]["egress_denied"] = True

    try:
        # Every task a slot can use is built or pulled once, serially, before any pair.
        prebuilt = await prebuild_images(
            [Path(entry["task_dir"]) for entry in [manifest["admission"], *manifest["cases"]]]
        )
        await asyncio.gather(pair(0), pair(1))
    except BaseException as exc:
        error = type(exc).__name__
        raise
    finally:
        cleanup_errors = []
        for environment in reversed(environments):
            try:
                await asyncio.wait_for(environment.stop(delete=True), timeout=120)
            except BaseException as exc:
                cleanup_errors.append(type(exc).__name__)
        cleanup = [
            base.resources_for_session(environment.session_id) for environment in environments
        ]
        passed = (
            error is None
            and len(observations) == 4
            and not cleanup_errors
            and all(row["complete"] for row in cleanup)
        )
        write(
            directory / "proof.json",
            {
                "passed": passed,
                "model_dispatches": 0,
                "concurrency": 2,
                "source_revision": require_source(),
                "finished_at": base.now(),
                "daemon": base.daemon_identity(),
                "prebuilt_images": prebuilt,
                "observations": observations,
                "cleanup": cleanup,
                "cleanup_errors": cleanup_errors,
                "error_type": error,
                "task_manifest_sha256": sha(MANIFEST),
                "runner_sha256": sha(Path(__file__)),
            },
        )
    assert passed
    print("Prebuilt task images; two concurrent agent/verifier pairs and cleanup passed; no model")


def require_collector() -> None:
    from scripts.eval.check_harbor_observations import validate_observations

    if "expected_effective_verify_mode" not in inspect.signature(validate_observations).parameters:
        raise ValueError("collector source fix must land before freezing this experiment")


def require_infrastructure() -> None:
    proof = read(ROOT / "infrastructure/proof.json")
    assert proof["passed"] is True and proof["model_dispatches"] == 0
    assert proof["source_revision"] == REVISION
    assert proof["runner_sha256"] == sha(Path(__file__))
    assert proof["task_manifest_sha256"] == sha(MANIFEST)
    assert proof["daemon"] == base.daemon_identity()
    assert proof.get("concurrency", 1) >= 2, "paired slots need a two-pair infrastructure proof"
    manifest = read(MANIFEST)
    assert {row["task"] for row in proof["prebuilt_images"] if row["role"] == "verifier"} >= {
        Path(entry["task_dir"]).name for entry in [manifest["admission"], *manifest["cases"]]
    }, "every task image must be prebuilt before paired slots"
    age = datetime.now(UTC) - datetime.fromisoformat(proof["finished_at"])
    assert 0 <= age.total_seconds() <= 86400, "infrastructure proof expired"


def frozen_inputs(phase: str) -> dict[str, str]:
    paths = [
        ROOT / name
        for name in (
            "runner.py",
            "protocol.md",
            "source-pin.json",
            "source-proof.json",
            "source.tar.gz",
            "offline-check.json",
            "infrastructure/proof.json",
            f"{phase}/schedule.proposed.json",
            f"{phase}/run-spec.proposed.json",
            *SHARED_FILES,
        )
    ]
    paths.extend((FIXTURE, MANIFEST))
    paths.extend(LEGACY_ROOT / name for name in PINS)
    paths.extend(path for path in (ROOT / "task-bundle").rglob("*") if path.is_file())
    paths.extend(path for path in (ROOT / "payloads").rglob("*") if path.is_file())
    for path in paths:
        assert path.is_file() and not path.is_symlink()
    return {str(path): sha(path) for path in sorted(set(paths))}


def check_cells(phase: str, cells: list[dict]) -> None:
    from evals.benchmarks.decision_handoff_runtime import inbox_request
    from harbor.models.task.task import Task

    cohort = read(FIXTURE)
    cases = {case["id"]: case for case in [cohort["admission"], *cohort["cases"]]}
    assert len(cells) == (2 if phase == "admission" else 6)
    for cell, expected in zip(cells, schedule(phase, read(MANIFEST)), strict=True):
        assert all(cell[key] == value for key, value in expected.items())
        task = Task(cell["task_dir"])
        payload = read(Path(cell["case_file"]))
        raw = cases[cell["case_id"]]
        assert payload["case"] == {
            **raw,
            "profile": "inbox",
            "request": inbox_request(raw["items"]),
        }
        assert payload["orders"] == cohort["orders"]
        assert read(Path(cell["task_dir"]) / "tests/case.json") == payload["case"]
        assert cell["task_checksum"] == task.checksum
        assert cell["case_sha256"] == sha(Path(cell["case_file"]))
        assert payload["intervention"] is None
        assert task.instruction == payload["case"]["request"]
        assert len(payload["case"]["items"]) == (2 if phase == "admission" else 12)
        assert str(task.config.environment.docker_image) == read(MANIFEST)["image_digest"]
        assert task.config.agent.timeout_sec == AGENT_TIMEOUT_S
        assert task.config.verifier.timeout_sec == 30
        assert sha(Path(cell["task_dir"]) / "tests/handoff_runtime.py") == sha(
            SOURCE / "evals/benchmarks/decision_handoff_runtime.py"
        ), "task oracle must match the newly pinned runtime"
        assert task.config.environment.network_mode == "public"
        assert task.config.verifier.environment.network_mode == "no-network"
        assert tuple(task.config.artifacts) == base.TRANSFER


def cell_pairs(cells: list[dict]) -> list[list[dict]]:
    return [cells[index : index + 2] for index in range(0, len(cells), 2)]


def phase_slots(phase: str, cells: list[dict]) -> list[Slot]:
    """This phase's E-track slots; tasks and launch orders must equal the prepared protocol."""
    rows = [json.loads(line) for line in SLOTS.read_text(encoding="utf-8").splitlines() if line]
    slots = load_slots(rows, UNIT_FOR_PHASE[phase], arm_c=False)
    pairs = cell_pairs(cells)
    if len(slots) != len(pairs) or any(
        slot.cell != "natural"
        or slot.repetition != 0
        or [arm.lower() for arm in slot.launch_order] != [cell["arm"] for cell in pair]
        or {cell["case_id"] for cell in pair} != {slot.task}
        for slot, pair in zip(slots, pairs, strict=False)
    ):
        raise ValueError(f"{phase}: slot matrix differs from the prepared protocol order")
    return slots


def intent_policy(cell: dict) -> dict:
    """Everything that must be equal for trials to combine (03 §5.1)."""
    astra = "openai/subscription/gpt-6-astra/xhigh"
    return {
        "root_route": astra,
        "reflection_route": astra,
        "final_judge": astra + " (raw rule_based, effective llm_judge)",
        "helper_route": astra if cell["arm"] == "a" else "typesafe/payg/jev-1.13.0/none",
        "tools": "analyze_request, lookup_order_status (read-only)",
        "task_checksum": cell["task_checksum"],
        "verifier_sha256": cell["verifier_sha256"],
        "budget": (
            f"root {ROOT_BUDGET_S}s/6 rounds; agent {AGENT_TIMEOUT_S}s; setup 600s; "
            f"verifier 30s; watchdog {WATCHDOG:g}s; cleanup 120s"
        ),
        "llm_max_retries": "1",
        "source_revision": REVISION,
    }


def freeze_cells(phase: str, cells: list[dict]) -> list[dict]:
    """Add slot identity, the five freeze digests and the derived Jev call cap."""
    from evals.benchmarks.decision_metrics import policy_digest, reset_digest

    caps = derive_jev_call_caps(SOURCE)
    frozen = []
    for slot, pair in zip(phase_slots(phase, cells), cell_pairs(cells), strict=True):
        for cell in pair:
            letter = cell["arm"].upper()
            entry = {
                **cell,
                "unit": UNIT_FOR_PHASE[phase],
                "slot_id": slot.slot_id,
                "slot_index": slot.slot_index,
                "arm_letter": letter,
                "verification_engine": cell["intent_target_engine"],
                "uses_jev": cell["arm"] == "b",
                "barrier": False,
                "replay_preselected": slot.replay_preselected,
                "replay_side": slot.replay_side(letter),
                "verifier_sha256": sha(Path(cell["task_dir"]) / "tests/verify.py"),
                "jev_call_cap": caps["helper_per_trial"] if cell["arm"] == "b" else 0,
            }
            entry["policy_digest"] = policy_digest(intent_policy(entry))
            entry["reset_digest"] = reset_digest(RESET_BOUNDARY)
            frozen.append(entry)
    return frozen


def freeze(phase: str) -> None:
    from evals.platforms.harbor_runtime import _verify_bundle
    from scripts.eval.contract import validate_run_spec

    if phase == "natural":
        require_admission_passed()
    require_source()
    require_collector()
    require_infrastructure()
    directory = ROOT / phase
    cells = read(directory / "schedule.proposed.json")
    check_cells(phase, cells)
    cells = freeze_cells(phase, cells)
    caps = derive_jev_call_caps(SOURCE)
    proof = read(ROOT / "source-proof.json")
    assert proof["runner_sha256"] == sha(Path(__file__))
    assert proof["protocol_sha256"] == sha(ROOT / "protocol.md")
    assert read(ROOT / "offline-check.json")["runner_sha256"] == sha(Path(__file__))
    bundle = ROOT / "source.tar.gz"
    assert sha(bundle) == proof["source_archive_sha256"]
    _verify_bundle(bundle, sha(bundle))
    with tarfile.open(bundle) as archive:
        assert archive.pax_headers["comment"] == REVISION
    spec = read(directory / "run-spec.proposed.json")
    assert spec["reproduction"]["execution"]["timeout_seconds"] == AGENT_TIMEOUT_S
    spec["preregistration"].update(
        status="frozen",
        frozen_at=base.now(),
        live_test_approved=True,
        operator="Parent reviewed source, protocol and provider-free gates; --freeze --reviewed",
    )
    write(directory / "run-spec.json", spec)
    write(directory / "host-environment.json", base.host_environment())
    validate_run_spec(directory / "run-spec.json")
    binding = frozen_inputs(phase)
    binding.update(
        {
            str(directory / name): sha(directory / name)
            for name in (
                "run-spec.json",
                "host-environment.json",
            )
        }
    )
    write(
        directory / "freeze.json",
        {
            "phase": phase,
            "frozen_at": spec["preregistration"]["frozen_at"],
            "source_revision": REVISION,
            "source_bundle": str(bundle),
            "source_sha256": sha(bundle),
            "harbor_version": "0.22.0",
            "root_budget_s": ROOT_BUDGET_S,
            "agent_timeout_s": AGENT_TIMEOUT_S,
            "watchdog_s": WATCHDOG,
            "sha256": binding,
            "unit": UNIT_FOR_PHASE[phase],
            "slot_width": 2,
            "cells": cells,
            "planned_astra_call_cap": spec["reproduction"]["execution"]["budget"]["limit"],
            "planned_jev_calls": sum(c["uses_jev"] for c in cells) * caps["judgments_per_trial"],
            "jev_call_caps": caps,
            "expected_effective_verify_mode": "llm_judge",
            "global_judgment_engine": "llm",
            "preselected_replay": {
                "case_id": "inbox-korean",
                "repetition": 0,
                "left_arm": "a",
                "right_arm": "b",
            },
        },
    )
    print(f"{phase}: frozen {len(cells)} cells; no inference")


def require_admission_passed() -> None:
    from scripts.eval.contract import validate_run_bundle

    directory = ROOT / "admission"
    validate_run_bundle(directory / "run-spec.json")
    result, frozen = read(directory / "results.json"), read(directory / "freeze.json")
    assert result["complete"] is True and result["primary"]["numerator"] == 2
    assert frozen["source_revision"] == REVISION
    assert all(sha(Path(path)) == digest for path, digest in frozen["sha256"].items())
    playback = read(directory / "playback-check.json")
    assert playback["played"] is True and playback["score_authority"] is False
    assert playback["source_revision"] == REVISION
    assert playback["admission_results_sha256"] == sha(directory / "results.json")
    assert playback["mode"] in {"ATIF-derived-player", "ATIF-derived-MP4"}
    expected = {
        str(Path("trials") / c["trial_name"] / "agent/recording.cast") for c in frozen["cells"]
    }
    assert len(playback["recordings"]) == 2
    assert {item["path"] for item in playback["recordings"]} == expected
    assert all(sha(directory / item["path"]) == item["sha256"] for item in playback["recordings"])


def preflight(phase: str) -> tuple[dict, dict]:
    from scripts.eval.contract import validate_run_spec

    require_source()
    require_collector()
    require_infrastructure()
    directory = ROOT / phase
    frozen = read(directory / "freeze.json")
    spec = validate_run_spec(directory / "run-spec.json")
    assert spec["preregistration"]["live_test_approved"] is True
    assert spec["reproduction"]["execution"]["timeout_seconds"] == AGENT_TIMEOUT_S
    assert frozen["root_budget_s"] == ROOT_BUDGET_S
    assert frozen["agent_timeout_s"] == AGENT_TIMEOUT_S
    assert frozen["watchdog_s"] == WATCHDOG
    assert frozen["source_revision"] == spec["reproduction"]["geode"]["revision"] == REVISION
    assert frozen["expected_effective_verify_mode"] == "llm_judge"
    assert frozen["global_judgment_engine"] == "llm"
    assert all(sha(Path(path)) == digest for path, digest in frozen["sha256"].items())
    assert read(directory / "host-environment.json") == base.host_environment()
    check_cells(phase, frozen["cells"])
    if frozen["cells"] != freeze_cells(
        phase, [{k: c[k] for k in SCHEDULE_KEYS} for c in frozen["cells"]]
    ):
        raise ValueError(f"{phase}: frozen slot, digest or Jev cap fields changed")
    if phase == "natural":
        require_admission_passed()
    return spec, frozen


_legacy_collect = base.collect


def collect(
    phase: str, spec: dict, frozen: dict, cell: dict, error: str | None, elapsed: float
) -> dict:
    from scripts.eval import check_harbor_observations as observations

    require_collector()
    # The pinned r6 collector predates this keyword. Scope its imported validator
    # to one synchronous collection; all native checks and evidence stay intact.
    validator = partial(
        observations.validate_observations, expected_effective_verify_mode="llm_judge"
    )
    with patch.object(observations, "validate_observations", validator):
        return _legacy_collect(phase, spec, frozen, cell, error, elapsed)


def helper_observation(row: dict, handoff: list[dict] | None, events: list[dict] | None) -> dict:
    """Observed helper facts (§3.1, user rule: a fallback never counts as helper success).

    admitted: the oracle's ``decision_succeeded`` (every analyze_request call returned an
    admitted decision). fallback_used: true when any structured_decision call was
    answered by a route whose (provider, model) differs from the arm's helper route
    (a: openai + gpt-6-astra; b: typesafe + jev-1.13.0), read from the terminal call
    events; null when calls and helper results do not pair up or a route field is
    missing. feedback_consumed: every analyze_request result reached a later root
    request. Anything not observed stays null, never a default.
    """
    oracle = (row.get("independent_verifier") or {}).get("oracle") or {}
    checks = oracle.get("checks") if isinstance(oracle.get("checks"), dict) else {}
    admitted = checks.get("decision_succeeded")
    fallback = consumed = None
    if isinstance(handoff, list):
        helpers = [
            r
            for r in handoff
            if r.get("kind") == "tool_result" and r.get("tool") == "analyze_request"
        ]
        roots = [r for r in handoff if r.get("kind") == "root_request"]
        if helpers:
            consumed = all(
                any(h.get("tool_call_id") in (root.get("tool_result_ids") or []) for root in roots)
                for h in helpers
            )
        if isinstance(events, list):
            answered = [
                e.get("payload") or {}
                for e in events
                if isinstance(e, dict)
                and e.get("action") == "llm.call.ended"
                and (e.get("payload") or {}).get("purpose") == "structured_decision"
            ]
            provider, model = HELPER_ROUTE[row["arm"]]
            if (
                helpers
                and len(answered) == len(helpers)
                and all(p.get("provider") and p.get("model") for p in answered)
            ):
                fallback = any(
                    p["provider"] != provider
                    or p["model"] != model
                    or p.get("response_model") not in (None, model)
                    for p in answered
                )
    return {
        "helper_admitted": admitted if type(admitted) is bool else None,
        "helper_fallback_used": fallback,
        "helper_feedback_consumed": consumed,
    }


def strict_success(row: dict) -> bool:
    oracle = row.get("independent_verifier", {}).get("oracle", {})
    helper = row.get("helper_observation") or {}
    return bool(
        row.get("valid") is True
        and row.get("passed") is True
        and helper.get("helper_admitted") is True
        and helper.get("helper_fallback_used") is False
        and helper.get("helper_feedback_consumed") is True
        and all(
            type(oracle.get(key)) is int and oracle[key] == 0
            for key in (
                "wrong_target_lookup_count",
                "extra_lookup_count",
                "false_completion_count",
            )
        )
    )


def reflection_coverage(handoff: list[dict]) -> dict:
    pending_tools = []
    rounds, final_ids = [], []
    for event in handoff:
        kind = event["kind"]
        if kind == "tool_result":
            pending_tools.append(event["tool_call_id"])
        elif kind == "reflection_request":
            assert pending_tools and event.get("llm_call_id")
            rounds.append(
                {"tool_result_ids": pending_tools, "reflection_call_id": event["llm_call_id"]}
            )
            pending_tools = []
        elif kind == "verification_request":
            assert not pending_tools and event.get("llm_call_id")
            final_ids.append(event["llm_call_id"])
        elif kind == "root_request" and event.get("request_role") != "replan":
            assert not pending_tools, "tool round lacks actual reflection request"
    assert not pending_tools and final_ids, "missing round or final reflection coverage"
    return {"tool_rounds": rounds, "final_call_ids": final_ids}


def seconds(value: object, *, scale: float = 1) -> float | None:
    """Observed positive duration only: a stored 0.0 may be a filled, unobserved value."""
    return (
        float(value) / scale
        if type(value) in (int, float) and math.isfinite(value) and value > 0
        else None
    )


def project_timings(row: dict, trial: Path) -> None:
    """Read existing timing evidence, including invalid trials; never impute a duration.

    Terminal call events persist the observer latency as ``payload.duration_ms``;
    missing, non-numeric, non-finite and non-positive values stay null.
    """
    documents = {}
    for name in ("call-events.json", "handoff.json"):
        try:
            value = read(trial / "agent" / name)
        except (OSError, ValueError):
            value = None
        documents[name] = value if isinstance(value, list) else []
    ends = [
        e
        for e in documents["call-events.json"]
        if isinstance(e, dict) and e.get("action") == "llm.call.ended"
    ]
    # Invalid trials may retain malformed runtime evidence; timing then stays
    # incomplete instead of raising before the cell's attempt row is written.
    runtime = row.get("runtime")
    accounting = runtime.get("call_accounting") if isinstance(runtime, dict) else None
    if not isinstance(accounting, list) or not all(isinstance(c, dict) for c in accounting):
        accounting = []
    attempt_counts = Counter(c.get("llm_attempt_id") for c in accounting)
    calls = []
    for call in accounting:
        identity = call.get("llm_attempt_id")
        matches = [e for e in ends if identity and e.get("llm_attempt_id") == identity]
        payload = matches[0].get("payload") if len(matches) == 1 else None
        payload = payload if isinstance(payload, dict) else {}
        calls.append(
            {
                "llm_attempt_id": identity,
                "purpose": call.get("purpose") or "unknown",
                "elapsed_seconds": seconds(payload.get("duration_ms"), scale=1000)
                if attempt_counts[identity] == 1 and payload.get("purpose") == call.get("purpose")
                else None,
            }
        )
    helpers = [
        e
        for e in documents["handoff.json"]
        if isinstance(e, dict)
        and e.get("kind") == "tool_result"
        and e.get("tool") == "analyze_request"
    ]
    helper_counts = Counter(h.get("tool_call_id") for h in helpers)
    row["timing_observations"] = {
        "calls": calls,
        "helper_tools": [
            {
                "tool_call_id": h.get("tool_call_id"),
                "elapsed_seconds": seconds(h.get("elapsed_seconds"))
                if h.get("tool_call_id") and helper_counts[h["tool_call_id"]] == 1
                else None,
            }
            for h in helpers
        ],
        "call_inventory_complete": bool(accounting) and len(ends) == len(accounting),
        "scope": "recorded attempts and helper invocations; overlapping durations, not wall time",
    }


def summarize_seconds(values: list[float | None], *, complete: bool) -> dict:
    observed = [value for value in values if value is not None]
    complete = bool(complete and values and len(observed) == len(values))
    return {
        "complete": complete,
        "total_seconds": sum(observed) if complete else None,
        "median_seconds": statistics.median(observed) if complete else None,
        "observed_sum_seconds": sum(observed) if observed else None,
        "observed_median_seconds": statistics.median(observed) if observed else None,
        "observed_entries": len(observed),
        "missing_entries": len(values) - len(observed),
    }


def project_metrics(row: dict, trial: Path, cell: dict) -> None:
    """Derive separate labels and actual consumers; never manufacture a matched-verifier file."""
    project_timings(row, trial)
    row["helper_observation"] = dict.fromkeys(HELPER_FIELDS)
    if not row.get("valid"):
        return
    from evals.benchmarks.decision_handoff_runtime import _inbox_decision_matches

    try:
        case = read(Path(cell["case_file"]))["case"]
        handoff = read(trial / "agent/handoff.json")
        try:
            events = read(trial / "agent/call-events.json")
        except (OSError, ValueError):
            events = None
        row["helper_observation"] = helper_observation(row, handoff, events)
        coverage = reflection_coverage(handoff)
        helper_rows = [
            r for r in handoff if r["kind"] == "tool_result" and r["tool"] == "analyze_request"
        ]
        roots = [r for r in handoff if r["kind"] == "root_request"]
        projected = []
        for item in case["items"]:
            entry = {"id": item["id"]}
            for name, helper in (
                ("initial", helper_rows[0] if helper_rows else None),
                ("final", helper_rows[-1] if helper_rows else None),
            ):
                decisions = (helper or {}).get("result", {}).get("result", {}).get("items", [])
                decision = next((d for d in decisions if d.get("id") == item["id"]), {})
                # Reuse the source-span check while measuring intent independently.
                target_only = {**decision, "intent": item["expected_intent"]}
                entry[name] = {
                    "intent_correct": decision.get("intent") == item["expected_intent"]
                    if helper
                    else None,
                    "target_correct": _inbox_decision_matches(item, target_only)
                    if helper
                    else None,
                    "intent": decision.get("intent"),
                    "target": decision.get("target"),
                    "tool_call_id": helper["tool_call_id"] if helper else None,
                }
            projected.append(entry)
        consumers = [
            {
                "tool": observed["tool"],
                "tool_call_id": observed["tool_call_id"],
                "root_call_ids": [
                    r["llm_call_id"]
                    for r in roots
                    if observed["tool_call_id"] in r["tool_result_ids"]
                ],
            }
            for observed in handoff
            if observed["kind"] == "tool_result"
        ]
        calls = row["runtime"]["call_accounting"]
        counts = {
            purpose: sum(c.get("purpose") == purpose for c in calls)
            for purpose in (
                "agentic_loop",
                "structured_decision",
                "cognitive_reflection",
                "turn_verification",
            )
        }
        row["semantic_metrics"] = {
            "strict_success": strict_success(row),
            **row["helper_observation"],
            "item_count": len(projected),
            "helper_observed": bool(helper_rows),
            "helper_tool_elapsed_seconds": [
                helper["elapsed_seconds"] for helper in row["timing_observations"]["helper_tools"]
            ],
            "items": projected,
            "tool_result_consumers": consumers,
            "call_counts": counts,
            "reflection_coverage": coverage,
            "oracle": row["independent_verifier"]["oracle"],
            "handoff_sha256": sha(trial / "agent/handoff.json"),
        }
    except Exception as exc:
        row.update(valid=False, passed=False, error_type="metric_projection_" + type(exc).__name__)


def summarize(phase: str, cells: list[dict], rows: list[dict]) -> dict:
    """One primary unit is an inbox, not a label, call, or trial retry."""
    complete = len(rows) == len(cells) and all(r.get("valid") is True for r in rows)
    assert len(cells) == (2 if phase == "admission" else 6)
    assert len({r["trial_name"] for r in rows}) == len(rows)
    assert [r["trial_name"] for r in rows] == [c["trial_name"] for c in cells[: len(rows)]]
    counts = {
        arm: {
            "canonical_passed": sum(
                r.get("passed") is True and r.get("valid") is True for r in rows if r["arm"] == arm
            ),
            "strict_passed": sum(strict_success(r) for r in rows if r["arm"] == arm),
        }
        for arm in ("a", "b")
    }
    numerator = (
        (counts["b"]["strict_passed"] - counts["a"]["strict_passed"])
        if phase == "natural"
        else sum(c["canonical_passed"] for c in counts.values())
    )
    return {
        "phase": phase,
        "complete": complete,
        "planned_cells": len(cells),
        "observed_cells": len(rows),
        "independent_cases": 3 if phase == "natural" else 1,
        "primary": {
            "value": numerator / (3 if phase == "natural" else 2) if complete else None,
            "numerator": numerator if complete else None,
            "denominator": (3 if phase == "natural" else 2) if complete else None,
        },
        "arms": counts,
        "actual_charge_usd": None,
    }


def analyze(
    phase: str,
    spec: dict,
    frozen: dict,
    rows: list[dict],
    attempts: list[dict],
    refs: list[dict],
    dispatch: dict | None = None,
) -> int:
    from evals.benchmarks.decision_handoff_runtime import _aggregate_accounting
    from scripts.eval.contract import validate_analysis

    directory = ROOT / phase
    result = summarize(phase, frozen["cells"], rows)
    complete = result["complete"]
    for arm, entry in result["arms"].items():
        selected = [r for r in rows if r["arm"] == arm]
        calls = [c for r in selected for c in r.get("runtime", {}).get("call_accounting", [])]
        latencies = [r["runtime"]["elapsed_seconds"] for r in selected if r.get("runtime")]
        entry.update(
            attempted=len(selected),
            valid=sum(r["valid"] for r in selected),
            median_runtime_seconds=statistics.median(latencies) if latencies else None,
            accounting=_aggregate_accounting(calls, complete=complete),
            by_purpose={
                p: _aggregate_accounting(
                    [c for c in calls if c.get("purpose") == p], complete=complete
                )
                for p in sorted({c.get("purpose", "unknown") for c in calls})
            },
        )
        timings = [r.get("timing_observations", {}) for r in selected]
        timed_calls = [call for timing in timings for call in timing.get("calls", [])]
        timed_helpers = [helper for timing in timings for helper in timing.get("helper_tools", [])]
        timing_complete = complete and all(t.get("call_inventory_complete") for t in timings)
        entry["timing"] = {
            "scope": "attempt/tool durations overlap; do not add to each other or to wall time",
            "llm_attempt_seconds_by_purpose": {
                purpose: summarize_seconds(
                    [c["elapsed_seconds"] for c in timed_calls if c["purpose"] == purpose],
                    complete=timing_complete,
                )
                for purpose in sorted({c.get("purpose") or "unknown" for c in calls})
            },
            "helper_tool_seconds": summarize_seconds(
                [h["elapsed_seconds"] for h in timed_helpers], complete=timing_complete
            ),
            "runtime_wall_seconds": summarize_seconds(
                [seconds(r.get("runtime", {}).get("elapsed_seconds")) for r in selected],
                complete=complete,
            ),
            "host_wall_seconds": summarize_seconds(
                [seconds(r.get("host_elapsed_seconds")) for r in selected], complete=complete
            ),
        }
        metrics = [
            r["semantic_metrics"] for r in selected if r["valid"] and "semantic_metrics" in r
        ]
        items = [item for metric in metrics for item in metric["items"]]
        entry["labels"] = {
            stage: {
                field: {
                    "correct": sum(i[stage][field] is True for i in items),
                    "observed": sum(type(i[stage][field]) is bool for i in items),
                    "planned_items": 36 if phase == "natural" else 2,
                }
                for field in ("intent_correct", "target_correct")
            }
            for stage in ("initial", "final")
        }
        entry["burden"] = {
            key: {
                "observed_sum": sum(m["oracle"][key] for m in metrics),
                "observed_trials": len(metrics),
            }
            for key in (
                "analysis_call_count",
                "rejudgment_call_count",
                "rejudged_item_count",
                "helper_correction_count",
                "helper_rejudgment_recovery_count",
                "lookup_attempt_count",
                "rejected_lookup_count",
                "extra_lookup_count",
                "wrong_target_lookup_count",
                "false_completion_count",
            )
        }
    result["paired_deltas"] = []
    for case_id in dict.fromkeys(c["case_id"] for c in frozen["cells"]):
        pair = {r["arm"]: r for r in rows if r["case_id"] == case_id and r["valid"]}
        if set(pair) == {"a", "b"}:
            result["paired_deltas"].append(
                {
                    "case_id": case_id,
                    "repetition": 0,
                    "strict_success_delta": int(strict_success(pair["b"]))
                    - int(strict_success(pair["a"])),
                    "canonical_success_delta": int(pair["b"]["passed"]) - int(pair["a"]["passed"]),
                    "runtime_seconds_delta": pair["b"]["runtime"]["elapsed_seconds"]
                    - pair["a"]["runtime"]["elapsed_seconds"],
                }
            )
    result["trials"] = [
        {k: r[k] for k in ("trial_name", "case_id", "arm", "valid", "passed")}
        | {"strict_passed": strict_success(r) if r["valid"] else None}
        for r in rows
    ]
    if dispatch is not None:
        result["dispatch"] = dispatch
    write(directory / "results.json", result)
    ref = {
        "kind": "native-result",
        "path": "results.json",
        "sha256": sha(directory / "results.json"),
    }
    refs.append(ref)
    answer = (
        "Completed this synthetic inbox diagnostic; canonical and strict success are separate."
        if complete
        else "Stopped with invalid or missing planned cells; primary counts are null."
    )
    aggregate_id = spec["run_id"] + "-aggregate"
    aggregate = {
        "schema_id": "geode.eval-attempt@1",
        "schema_version": 1,
        "run_id": spec["run_id"],
        "attempt_id": aggregate_id,
        "parent_attempt_id": attempts[-1]["attempt_id"] if attempts else None,
        "sequence": len(attempts),
        "timing": {
            "status": "exact",
            "started_at": base.now(),
            "finished_at": base.now(),
            "source_ref": None,
        },
        "validity": "valid" if complete else "invalid",
        "outcome": "mixed" if complete else "unknown",
        "change": {
            "surface": "analysis-only",
            "description": "Frozen two-arm inbox aggregation; zero runtime dispatches.",
        },
        "expected_effect": "Apply the frozen denominator without replacing native reward.",
        "observed_result": answer,
        "failure_class": None if complete else "incomplete_planned_cells",
        "error_ref": None,
        "evidence_refs": [ref],
        "selected_for_analysis": True,
    }
    base.append(directory / "attempts.jsonl", aggregate)
    metric = {
        "name": spec["study"]["primary_metric"]["name"],
        **result["primary"],
        "unit": "ratio",
        "source_ref": "results.json",
        "source_locator": {key: "/primary/" + key for key in ("value", "numerator", "denominator")}
        if complete
        else None,
    }
    if not complete:
        metric["value"] = "not-measurable"
    write(
        directory / "analysis.json",
        {
            "schema_id": "geode.eval-analysis@1",
            "schema_version": 1,
            "run_id": spec["run_id"],
            "analyzed_at": base.now(),
            "run_spec_sha256": sha(directory / "run-spec.json"),
            "attempts_sha256": sha(directory / "attempts.jsonl"),
            "selected_attempt_ids": [a["attempt_id"] for a in attempts] + [aggregate_id],
            "answer": answer,
            "metrics": [metric],
            "decision": {
                "outcome": "diagnostic-only",
                "hypothesis_status": "mixed" if complete else "invalidated",
                "rationale": "Known synthetic workload; one repeat; no promotion authority.",
            },
            "limitations": [
                "Three author-visible inboxes, not sealed held-out tasks.",
                "Intent and source-bound target are offloaded; root rollouts are independent.",
                "Recorded usage and tariff estimates do not establish actual provider charges.",
                "ATIF-derived replay is not raw PTY or score authority.",
            ],
            "evidence_refs": refs,
        },
    )
    validate_analysis(
        directory / "analysis.json",
        run_spec_path=directory / "run-spec.json",
        attempts_path=directory / "attempts.jsonl",
    )
    return 0 if complete else 1


# Reuse the fixed native child, key lifecycle and evidence writer; paired slots
# (execute below) replace the serial r6 dispatch loop.
base.preflight, base.collect = preflight, collect
base.collect_semantic_metrics, base.analyze = project_metrics, analyze


def collect_arm(phase: str, spec: dict, frozen: dict, cell: dict, run) -> dict:
    """One finished arm: the pinned r6 collector, this study's projection and slot fields."""
    from evals.benchmarks.jev_cost_ledger import jev_calls_from_call_accounting

    error = run.error or (None if run.exit_code in (0, None) else "child_nonzero")
    elapsed = (
        None
        if run.launched_at is None or run.exited_at is None
        else round(run.exited_at - run.launched_at, 3)
    )
    trial = ROOT / phase / "trials" / cell["trial_name"]
    row = collect(phase, spec, frozen, cell, error, elapsed)
    project_metrics(row, trial, cell)
    try:
        native = read(trial / "result.json") if (trial / "result.json").is_file() else None
    except (OSError, ValueError):
        native = None
    row["agent_start_utc"], row["agent_end_utc"] = agent_interval(native)
    return finish_row(row, cell, jev_calls_from_call_accounting)


def finish_row(row: dict, cell: dict, jev_calls) -> dict:
    row["validity"] = "valid" if row["valid"] else "invalid"
    row["outcome"] = ("passed" if row["passed"] else "failed") if row["valid"] else "unknown"
    row["failure_class"] = (
        None
        if row["valid"] and row["passed"]
        else "semantic_failure"
        if row["valid"]
        else row.get("error_type") or row.get("collection_error_type") or "invalid"
    )
    unknown = [{"call_id": None, "input_tokens": None}] * int(cell["jev_call_cap"])
    if not cell["uses_jev"]:
        row["jev_calls"] = []
    else:
        calls = (row.get("runtime") or {}).get("call_accounting")
        try:
            row["jev_calls"] = jev_calls(calls) if isinstance(calls, list) else unknown
        except (TypeError, ValueError):
            row["jev_calls"] = unknown
    return row


class IntentState:
    """Write each finished slot: trial receipts, r6-format attempts and private receipts."""

    def __init__(self, phase, spec, frozen, *, account, jev, quota_start, proof_sha256):
        self.phase, self.spec, self.frozen = phase, spec, frozen
        self.account, self.jev, self.quota_start = account, jev, quota_start
        self.directory = ROOT / phase
        self.proof_sha256 = proof_sha256
        self.cells = {(c["slot_id"], c["arm_letter"]): c for c in frozen["cells"]}
        self.rows, self.attempts, self.refs, self.reports = [], [], [], []

    def record(self, report) -> None:
        from scripts.eval.contract import validate_attempts

        self.reports.append(report)
        for letter in report.slot.launch_order:
            cell = self.cells[(report.slot.slot_id, letter)]
            run, row = report.runs[letter], report.rows[letter]
            for key, value in cell.items():  # dispatcher-made rows (prepare failure) lack the cell
                row.setdefault(key, value)
            row.setdefault("valid", False)
            row.setdefault("passed", False)
            row.setdefault("helper_observation", dict.fromkeys(HELPER_FIELDS))
            trial = self.directory / "trials" / cell["trial_name"]
            trial.mkdir(parents=True, exist_ok=True, mode=0o700)
            row["concurrency"] = report.concurrency_fields(letter)
            write(trial / "trial-receipt.json", json.loads(json.dumps(row, default=str)))
            refs = base.evidence(self.directory, trial)
            started = run.host_launch_utc or base.now()
            attempt = {
                "schema_id": "geode.eval-attempt@1",
                "schema_version": 1,
                "run_id": self.spec["run_id"],
                "attempt_id": f"{self.spec['run_id']}-a{cell['index']:04}",
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
                    "surface": self.phase,
                    "description": f"{report.slot.slot_id} {cell['case_id']}, arm {cell['arm']}, "
                    "repeat 0; paired concurrent slot; no retry",
                },
                "expected_effect": self.spec["study"]["hypothesis"],
                "observed_result": "See native verifier and private trial receipt; semantic "
                "outcome is separate from measurement validity.",
                "failure_class": row["failure_class"],
                "error_ref": None,
                "evidence_refs": refs,
                "selected_for_analysis": True,
            }
            base.append(self.directory / "attempts.jsonl", attempt)
            validate_attempts(self.directory / "attempts.jsonl")
            helper = row.get("helper_observation") or {}
            write_private_receipt(
                self.directory,
                private_receipt(
                    report,
                    letter,
                    cell=cell,
                    attempt=attempt,
                    context={
                        "run_id": self.spec["run_id"],
                        "unit": UNIT_FOR_PHASE[self.phase],
                        "source_revision": REVISION,
                        "harbor_version": self.frozen["harbor_version"],
                        "image_digest": read(MANIFEST)["image_digest"],
                        "infra_proof_sha256": self.proof_sha256,
                        "host_environment_sha256": sha(self.directory / "host-environment.json"),
                    },
                    account=self.account,
                    jev=self.jev,
                    quota_start=self.quota_start,
                    extra={name: helper.get(name) for name in HELPER_FIELDS},
                ),
            )
            self.rows.append(row)
            self.attempts.append(attempt)
            self.refs.extend(refs)
        base.append(self.directory / "slots.jsonl", report.summary())


def stop_phase(directory: Path, failure: str, reason: str, **extra) -> None:
    record = {"failure_class": failure, "reason": reason, "at": base.now(), **extra}
    write(directory / f"unit-stop-{datetime.now(UTC):%Y%m%dT%H%M%SZ}.json", record)
    print(json.dumps({"unit_stopped": failure, "reason": reason}))


async def execute(phase: str, *, quota_live: bool) -> int:
    """Paired concurrent slots (05 v2 §2.4) with the host lock and every slot guard."""
    import time

    from evals.benchmarks.jev_cost_ledger import (
        JevBudgetRefusedError,
        JevCostLedger,
        JevLedgerError,
        jev_calls_from_call_accounting,
    )

    spec, frozen = preflight(phase)
    unit, directory, run_id = UNIT_FOR_PHASE[phase], ROOT / phase, spec["run_id"]
    lock = ExecutionLock(RUN_ROOT, mode="e2e-slot", run_id=run_id)
    try:
        lock.acquire()
    except ScheduleOverlapError as error:
        stop_phase(directory, "schedule_overlap", str(error), holder=error.holder)
        return 3
    try:
        slots = phase_slots(phase, frozen["cells"])
        try:
            claims = account_fields(read_account_claims(codex_auth_file()), now=time.time())
        except (OSError, ValueError) as error:
            stop_phase(directory, "account_unreadable", type(error).__name__)
            return 3
        required = int(len(slots) * (WATCHDOG + CLEANUP) + AUTH_MARGIN_SLACK_S)
        refusal = account_refusal(claims, required_margin_s=required)
        if refusal:
            stop_phase(directory, refusal, "account guard refused the unit")
            return 3
        try:
            quota = QuotaLedger(QUOTA_LEDGER)
        except (OSError, ValueError) as error:
            stop_phase(directory, "quota_ledger_unavailable", type(error).__name__)
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
            stop_phase(directory, "quota_" + start["decision"].replace("-", "_"), start["notes"])
            return 3
        try:
            ledger = JevCostLedger.open(JEV_LEDGER)
            ledger.admit_unit(run_id, frozen["planned_jev_calls"])
        except JevBudgetRefusedError as error:
            stop_phase(directory, "jev_budget_refused", error.reason)
            return 3
        except (OSError, ValueError, JevLedgerError) as error:
            stop_phase(directory, "jev_ledger_unavailable", type(error).__name__)
            return 3
        proof = ROOT / "infrastructure/proof.json"
        write(
            directory / "dispatch-lock.json",
            {
                "started_at": base.now(),
                "freeze_sha256": sha(directory / "freeze.json"),
                "infra_proof_sha256": sha(proof),
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
        state = IntentState(
            phase,
            spec,
            frozen,
            account=account,
            jev=jev,
            quota_start=start,
            proof_sha256=sha(proof),
        )
        guards = [
            LockGuard(lock),
            StopFileGuard(directory),
            PreflightGuard(lambda: preflight(phase)),
            account,
            QuotaGuard(quota, unit, slots, frozen["planned_astra_call_cap"], reader),
            jev,
        ]

        async def collect_slot(slot: Slot, run) -> dict:
            cell = cells[(slot.slot_id, run.arm)]
            try:
                return await asyncio.to_thread(collect_arm, phase, spec, frozen, dict(cell), run)
            except Exception as error:
                # Last resort: the slot is still recorded, guarded and settled (unknown Jev calls).
                failure = "collection_" + type(error).__name__
                row = {**cell, "valid": False, "passed": False, "error_type": failure}
                row["helper_observation"] = dict.fromkeys(HELPER_FIELDS)
                return finish_row(row, cell, jev_calls_from_call_accounting)

        driver = SubprocessDriver(
            cells=cells,
            runner=ROOT / "runner.py",
            mode_args=["--phase", phase],
            directory=directory,
            pythonpath=SOURCE,
            key_file=base.key_file,
            cleanup_s=CLEANUP,
        )
        dispatcher = PairedDispatcher(
            driver=driver,
            collect=collect_slot,
            guards=guards,
            on_slot=state.record,
            watchdog_s=WATCHDOG,
        )
        report = await dispatcher.run(slots)
        code = analyze(
            phase,
            spec,
            frozen,
            state.rows,
            state.attempts,
            state.refs,
            dispatch={**report.summary(), "slots": [r.summary() for r in state.reports]},
        )
        astra = [
            c
            for r in state.rows
            for c in (r.get("runtime") or {}).get("call_accounting", [])
            if c.get("model") == "gpt-6-astra"
        ]
        quota.end_record(
            unit=unit,
            snapshot=live_snapshot() if quota_live else None,
            start_used_pct=float(start["used_pct"]) if start.get("used_pct") else None,
            unit_astra_calls=len(astra),
            unit_astra_input_tokens=sum(
                int((c.get("usage") or {}).get("input_tokens") or 0) for c in astra
            ),
            account=claims,
            checkpoint_id=f"{unit}-end",
        )
        print(json.dumps({"phase": phase, **report.summary()}))
        return code
    finally:
        lock.release()


def self_test() -> None:
    """No archive, Docker, key access, network, freeze, or inference required."""
    manifest = {
        "admission": {"case_id": "inbox-admission", "task_dir": "a", "case_file": "a"},
        "cases": [
            {"case_id": "inbox-" + case, "task_dir": case, "case_file": case}
            for case in ("explicit", "context", "korean")
        ],
    }
    with (
        patch("socket.socket.connect", side_effect=AssertionError("offline self-test")),
        patch("socket.create_connection", side_effect=AssertionError("offline self-test")),
        patch.object(base, "key_file", side_effect=AssertionError("no credentials in self-test")),
    ):
        natural = schedule("natural", manifest)
        assert [c["arm"] for c in natural] == ["a", "b", "b", "a", "a", "b"]
        assert len(schedule("admission", manifest)) == 2
        assert base.child.__module__ == base.dispatch.__module__ == "intent_runner"
        assert base.collect is collect and base.preflight is preflight
        # Dispatched children run ROOT/runner.py with PYTHONPATH=SOURCE: same pin file.
        assert (base.ROOT, base.SOURCE, writer.SOURCE) == (ROOT, SOURCE, SOURCE)
        assert PIN_FILE.parent == ROOT and FIXTURE.is_relative_to(SOURCE)
        pinned = json.loads(PIN_FILE.read_text(encoding="utf-8"))
        assert (
            load_source_pin() == (SOURCE, REVISION) == (Path(pinned["source"]), pinned["revision"])
        )
        with tempfile.TemporaryDirectory(prefix="jev-intent-pin-") as scratch:
            trial_pin = Path(scratch) / "source-pin.json"
            with patch.dict(globals(), {"PIN_FILE": trial_pin}):
                for malformed_pin in (
                    None,
                    {k: v for k, v in pinned.items() if k != "created_at"},
                    {**pinned, "schema": "geode.jev-runner-source-pin@0"},
                    {**pinned, "revision": "A" * 40},
                    {**pinned, "source": "relative/checkout"},
                    {**pinned, "created_at": "2026-09-26T00:00:00"},
                    {**pinned, "extra": True},
                ):
                    trial_pin.unlink(missing_ok=True)
                    if malformed_pin is not None:
                        trial_pin.write_text(json.dumps(malformed_pin), encoding="utf-8")
                    try:
                        load_source_pin()
                    except SystemExit:
                        pass
                    else:
                        raise AssertionError("missing or malformed source pin was accepted")
                trial_pin.write_text(json.dumps(pinned), encoding="utf-8")
                assert load_source_pin() == (SOURCE, REVISION)
                before = trial_pin.read_bytes()
                for revision in ("A" * 40, "0" * 40, REVISION):
                    try:
                        pin_source(SOURCE, revision)
                    except SystemExit:
                        pass
                    else:
                        raise AssertionError("source pin was overwritten or written unverified")
                    assert trial_pin.read_bytes() == before
        oracle = {
            "wrong_target_lookup_count": 0,
            "extra_lookup_count": 0,
            "false_completion_count": 0,
        }
        helper_ok = {
            "helper_admitted": True,
            "helper_fallback_used": False,
            "helper_feedback_consumed": True,
        }
        rows = [
            {
                **c,
                "valid": True,
                "passed": True,
                "independent_verifier": {"oracle": dict(oracle)},
                "helper_observation": dict(helper_ok),
            }
            for c in natural
        ]
        assert summarize("natural", natural, rows)["primary"] == {
            "value": 0,
            "numerator": 0,
            "denominator": 3,
        }
        rows[0]["independent_verifier"]["oracle"]["extra_lookup_count"] = 1
        value = summarize("natural", natural, rows)
        assert value["arms"]["a"] == {"canonical_passed": 3, "strict_passed": 2}
        assert value["primary"]["value"] == 1 / 3
        rows[0]["valid"] = False
        assert summarize("natural", natural, rows)["primary"] == {
            "value": None,
            "numerator": None,
            "denominator": None,
        }
        assert summarize("natural", natural, rows[:2])["complete"] is False
        missing = {**rows[1], "independent_verifier": {"oracle": {}}}
        assert strict_success(missing) is False
        for name, value in (
            ("helper_admitted", None),
            ("helper_fallback_used", True),
            ("helper_fallback_used", None),
            ("helper_feedback_consumed", False),
        ):
            unobserved = {**rows[1], "helper_observation": {**helper_ok, name: value}}
            assert strict_success(unobserved) is False, name
        # Exercise the real collection adapter with fake leaves, without a source freeze.
        from scripts.eval import check_harbor_observations as observations

        def checker(*args, expected_effective_verify_mode=None, **kwargs):
            assert expected_effective_verify_mode == "llm_judge"
            return {"observation_valid": True}

        def collector(*args):
            return observations.validate_observations(Path("unused"))

        with (
            patch.object(observations, "validate_observations", checker),
            patch.dict(globals(), {"_legacy_collect": collector}),
        ):
            assert collect("natural", {}, {}, {}, None, 0)["observation_valid"] is True
        # A rejected natural admission must precede every source gate and write.
        with patch.dict(
            globals(),
            {
                "require_admission_passed": Mock(
                    side_effect=ValueError("admission or playback incomplete")
                ),
                "require_source": Mock(
                    side_effect=AssertionError("source gate reached before admission")
                ),
                "write": Mock(side_effect=AssertionError("write before admission")),
            },
        ):
            try:
                freeze("natural")
            except ValueError as error:
                assert str(error) == "admission or playback incomplete"
            else:
                raise AssertionError("natural freeze bypassed admission")
        # A source-independent in-memory inbox verifies the real ID projection.
        item = {
            "id": "test",
            "request": "Status A-104?",
            "candidates": ["A-104"],
            "expected_intent": "status_only",
            "expected_order": "A-104",
        }
        decision = {
            "id": "test",
            "intent": "cancel",
            "target": {"order_id": "A-104", "start": 7, "end": 12},
            "source_sha256": hashlib.sha256(item["request"].encode()).hexdigest(),
        }
        handoff = [
            {
                "kind": "tool_result",
                "tool": "analyze_request",
                "tool_call_id": "h1",
                "elapsed_seconds": 2.5,
                "result": {"result": {"items": [decision]}},
            },
            {"kind": "reflection_request", "llm_call_id": "c1"},
            {"kind": "root_request", "llm_call_id": "r2", "tool_result_ids": ["h1"]},
            {
                "kind": "tool_result",
                "tool": "analyze_request",
                "tool_call_id": "h2",
                "result": {"result": {"items": [{**decision, "intent": "status_only"}]}},
            },
            {"kind": "reflection_request", "llm_call_id": "c2"},
            {"kind": "root_request", "llm_call_id": "r3", "tool_result_ids": ["h1", "h2"]},
            {"kind": "verification_request", "llm_call_id": "v1"},
        ]
        sample = {**rows[1], "runtime": {"call_accounting": []}}
        with patch.dict(
            globals(),
            {
                "read": lambda p: (
                    handoff if p.name == "handoff.json" else {"case": {"items": [item]}}
                ),
                "sha": lambda p: "0" * 64,
            },
        ):
            project_metrics(sample, Path("not-a-run"), {"case_file": "synthetic"})
        assert sample["valid"] is True
        projected = sample["semantic_metrics"]
        assert projected["items"][0]["initial"]["intent_correct"] is False
        assert projected["items"][0]["initial"]["target_correct"] is True
        assert projected["items"][0]["final"]["intent_correct"] is True
        assert projected["tool_result_consumers"][0]["root_call_ids"] == ["r2", "r3"]
        assert len(projected["reflection_coverage"]["tool_rounds"]) == 2
        assert projected["helper_tool_elapsed_seconds"] == [2.5, None]
        assert sample["timing_observations"]["helper_tools"] == [
            {"tool_call_id": "h1", "elapsed_seconds": 2.5},
            {"tool_call_id": "h2", "elapsed_seconds": None},
        ]
        # Per-attempt observer time is distinct from inclusive helper tool time.
        timing_row = {
            "valid": False,
            "runtime": {
                "call_accounting": [
                    {"llm_attempt_id": "l1", "purpose": "structured_decision"},
                    {"llm_attempt_id": "l2", "purpose": "turn_verification"},
                    {"llm_attempt_id": "l3", "purpose": "agentic_loop"},
                    {"llm_attempt_id": "l4", "purpose": "cognitive_reflection"},
                ]
            },
        }
        # Persisted terminal payloads carry duration_ms; 0 may be a filled unknown and a
        # bare observer latency_ms key is not the persisted field.
        terminal_events = [
            {
                "action": "llm.call.ended",
                "llm_attempt_id": identity,
                "payload": {"purpose": purpose, **latency},
            }
            for identity, purpose, latency in (
                ("l1", "structured_decision", {"duration_ms": 2000}),
                ("l2", "turn_verification", {"duration_ms": None}),
                ("l3", "agentic_loop", {"duration_ms": 0}),
                ("l4", "cognitive_reflection", {"latency_ms": 1500}),
            )
        ]
        with patch.dict(
            globals(),
            {"read": lambda p: terminal_events if p.name == "call-events.json" else handoff},
        ):
            project_timings(timing_row, Path("not-a-run"))
            times = timing_row["timing_observations"]
            observed = [c["elapsed_seconds"] for c in times["calls"]]
            assert observed == [2, None, None, None]
            assert times["call_inventory_complete"] is True
            assert timing_row["valid"] is False
            incomplete_timing = summarize_seconds(observed, complete=True)
            assert incomplete_timing["total_seconds"] is None
            assert incomplete_timing["observed_sum_seconds"] == 2
            assert incomplete_timing["missing_entries"] == 3
            assert summarize_seconds([2, 4], complete=True)["median_seconds"] == 3
            assert summarize_seconds([2, 4], complete=False)["total_seconds"] is None
            assert summarize_seconds([], complete=True)["observed_sum_seconds"] is None
            terminal_events.append(terminal_events[0])
            project_timings(timing_row, Path("not-a-run"))
            assert timing_row["timing_observations"]["calls"][0]["elapsed_seconds"] is None
            assert timing_row["timing_observations"]["call_inventory_complete"] is False
            malformed = {"valid": False, "runtime": ["not", "an", "object"]}
            project_timings(malformed, Path("not-a-run"))
            assert malformed["timing_observations"]["calls"] == []
            assert malformed["timing_observations"]["call_inventory_complete"] is False
        assert all(
            seconds(v) is None
            for v in (None, True, False, 0, 0.0, -1, "5", float("nan"), float("inf"))
        )
        omitted = {**sample, "passed": False}
        with patch.dict(
            globals(),
            {
                "read": lambda p: (
                    [{"kind": "verification_request", "llm_call_id": "v1"}]
                    if p.name == "handoff.json"
                    else {"case": {"items": [item]}}
                ),
                "sha": lambda p: "0" * 64,
            },
        ):
            project_metrics(omitted, Path("not-a-run"), {"case_file": "synthetic"})
        assert omitted["valid"] is True and omitted["passed"] is False
        assert omitted["semantic_metrics"]["items"][0]["initial"]["intent_correct"] is None
        for missing_kind in ("reflection_request", "verification_request"):
            try:
                reflection_coverage([r for r in handoff if r["kind"] != missing_kind])
            except AssertionError:
                pass
            else:
                raise AssertionError("missing actual reflection evidence was accepted")
        # Validate real attempt/analysis schemas in a disposable local directory.
        # These are synthetic validator fixtures, never frozen run evidence.
        from scripts.eval.contract import validate_run_spec

        for incomplete in (False, True):
            with tempfile.TemporaryDirectory(prefix="jev-intent-offline-") as scratch:
                root = Path(scratch)
                directory = root / "natural"
                directory.mkdir()
                manifest_path = root / "manifest.json"
                write(manifest_path, manifest)
                with patch.dict(globals(), {"ROOT": root, "MANIFEST": manifest_path}):
                    spec = proposed_spec("natural", natural)
                    spec["preregistration"].update(status="frozen", frozen_at=base.now())
                    write(directory / "run-spec.json", spec)
                    validate_run_spec(directory / "run-spec.json")
                    check_rows, attempts, refs = [], [], []
                    for index, cell in enumerate(natural):
                        valid = not incomplete or index != 0
                        row = {
                            **cell,
                            "valid": valid,
                            "passed": valid,
                            "independent_verifier": {"oracle": dict(oracle)},
                            "runtime": {"elapsed_seconds": 1, "call_accounting": []},
                            "helper_observation": dict(helper_ok),
                        }
                        if index == 1:
                            row["independent_verifier"]["oracle"]["extra_lookup_count"] = 1
                        check_rows.append(row)
                        leaf = directory / f"synthetic-{index}.json"
                        write(leaf, {"synthetic_fixture": True, "valid": valid})
                        ref = {"kind": "native-result", "path": leaf.name, "sha256": sha(leaf)}
                        refs.append(ref)
                        attempt = {
                            "schema_id": "geode.eval-attempt@1",
                            "schema_version": 1,
                            "run_id": spec["run_id"],
                            "attempt_id": f"fixture-{index}",
                            "parent_attempt_id": None,
                            "sequence": index,
                            "timing": {
                                "status": "exact",
                                "started_at": base.now(),
                                "finished_at": base.now(),
                                "source_ref": None,
                            },
                            "validity": "valid" if valid else "invalid",
                            "outcome": "passed" if valid else "unknown",
                            "change": {
                                "surface": "offline-unit-fixture",
                                "description": "No actual model or task execution.",
                            },
                            "expected_effect": "Validate analysis contract.",
                            "observed_result": "Synthetic fixture only.",
                            "failure_class": None if valid else "synthetic_invalid",
                            "error_ref": None,
                            "evidence_refs": [ref],
                            "selected_for_analysis": True,
                        }
                        attempts.append(attempt)
                        base.append(directory / "attempts.jsonl", attempt)
                    assert analyze(
                        "natural", spec, {"cells": natural}, check_rows, attempts, refs
                    ) == int(incomplete)
                    output = read(directory / "results.json")
                    assert output["primary"]["denominator"] == (None if incomplete else 3)
                    assert output["primary"]["value"] == (None if incomplete else -1 / 3)
                    # Invalid cells and the aggregate row stay selected; none is dropped.
                    written = [
                        json.loads(line)
                        for line in (directory / "attempts.jsonl").read_text().splitlines()
                    ]
                    assert [a["attempt_id"] for a in written] == [
                        a["attempt_id"] for a in attempts
                    ] + [spec["run_id"] + "-aggregate"]
                    assert all(a["selected_for_analysis"] is True for a in written)
                    assert read(directory / "analysis.json")["selected_attempt_ids"] == [
                        a["attempt_id"] for a in written
                    ]
        print(
            "offline self-test PASS: 2/6 schedule, strict/native split, null primary, "
            "collector keyword, pinned native reuse, consumer IDs and analysis schemas; "
            "source pin gates, duration_ms timing with null/non-positive/duplicate "
            "regression, all attempts selected and natural-freeze admission regression"
        )


def main() -> int:
    if not __debug__:
        raise RuntimeError("Do not disable preparation checks")
    os.umask(0o077)
    ROOT.chmod(0o700)
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--self-check", action="store_true")
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--infra-preflight", action="store_true")
    mode.add_argument("--freeze", action="store_true")
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--child", type=int, help=argparse.SUPPRESS)
    parser.add_argument("--phase", choices=("admission", "natural"), default="admission")
    parser.add_argument("--reviewed", action="store_true")
    parser.add_argument("--secret-file", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--quota-live", action="store_true", help="user-approved WHAM lookup")
    args = parser.parse_args()
    if args.prepare:
        prepare()
    elif args.self_check:
        self_check()
    elif args.self_test:
        self_test()
    elif args.infra_preflight:
        if not args.reviewed:
            parser.error("parent review required before infrastructure startup")
        asyncio.run(infrastructure())
    elif args.freeze:
        if not args.reviewed:
            parser.error("source/spec/live authorization review required before freeze")
        freeze(args.phase)
    elif args.preflight:
        preflight(args.phase)
    elif args.child is not None:
        return asyncio.run(base.child(args.phase, args.child, args.secret_file))
    elif args.execute:
        if not args.reviewed:
            parser.error("parent review required before model dispatch")
        return asyncio.run(execute(args.phase, quota_live=args.quota_live))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
