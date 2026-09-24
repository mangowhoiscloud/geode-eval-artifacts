#!/usr/bin/env python3
"""Prepare reviewed public views; never dispatch models or edit source evidence.

Requires an installed GEODE checkout on PYTHONPATH. The private sources are
operator-supplied, not downloaded. Public files are deterministic for --prepared-at.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import statistics
import subprocess
import sys
import tarfile
from pathlib import Path

from core.observability.trajectory import verify_trajectory_integrity
from core.observability.trajectory_release import (
    _PUBLIC_SCAN_PATTERNS,
    stage_trajectory_release,
    verify_trajectory_release,
)
from scripts.eval.contract import validate_publication, validate_run_bundle

COHORTS = {
    "natural": "jev-verdict-20260923-r2/natural",
    "snapshots": "jev-verdict-snapshots-20260923",
    "recovery": "jev-verdict-recovery-20260924-r3/recovery",
    "admission/natural": "jev-verdict-20260923-r2/admission",
    "admission/recovery": "jev-verdict-recovery-20260924/admission",
    "invalid/collector": "jev-verdict-20260923/admission",
    "invalid/recovery-original": "jev-verdict-recovery-20260924/recovery",
    "invalid/recovery-r2": "jev-verdict-recovery-20260924-r2/recovery",
}
OMIT = {
    "system_prompt",
    "raw_answer",
    "raw_answer_retention",
    "root_outputs",
    "state",
    "final_text",
    "tool_definitions",
    "tool_calls",
    "projected_payload",
    "reasoning_items",
    "reasoning_summaries",
    "codex_output_items",
    "config",
    "step_results",
    "exception_info",
    "trial_uri",
    "task_id",
    "task_dir",
    "case_file",
    "db_path",
    "payload",
    "native",
    "effective",
    "candidate_output",
    "answer",
    "response_id",
    "rollout_details",
    "consumed_feedback",
    "actor_id",
    "entity_id",
    "session_key",
    "block_reason",
    "reflection_hint",
}
TEXT_FIELDS = set(
    "_redacted_fields action actor_type adapter arm attempt_id authority blockers "
    "candidate_call_id case_id choice classification collection_error_type comparison "
    "currency dispatch_mode effort engine entity_type error_type event "
    "expected_initial_verdict expected_verdict finished_at geode_session_id handoff_arm "
    "id initial_feedback_consumers initial_verdict kind latency_authority level "
    "limitation limits llm_attempt_id llm_call_id missing_token_fields model name "
    "native_exception_type observation_status phase profile profile_scope provider "
    "purpose recorded_attempts_scope recorded_attempts_timestamp_unit replay_status "
    "required_tools response_model response_provider retention_class run_id runtime "
    "runtime_scope scope score_authority session_id source source_revision stage "
    "started_at status step_id task_name termination_reason tool_call_id "
    "tracker_cost_authority trial trial_name turn_id type unit value verdict "
    "verification_engine verifier_environment_mode verify_mode version when workload_profile".split()
)
# File-level admission is closed; newly appearing top-level fields stop the
# normalizer for review instead of silently widening a publication boundary.
FIELDS = {
    "run-spec.json": "schema_id schema_version run_id created_at preregistration study reproduction artifacts privacy",
    "results.json": "phase complete planned_cells observed_cells independent_inboxes independent_task_families paired_conditions primary arms actual_charge_usd paired_deltas trials mock logical_calls source_revision correct rows setup_error accounting",
    "trial-receipt.json": "index case_id arm verification_engine repetition position task_dir case_file trial_name task_name task_checksum case_sha256 valid passed error_type host_elapsed_seconds actual_charge_usd intervention_delivered runtime native_reward independent_verifier replay semantic_metrics item_metrics collection_error_type invalid_trial_audit native_exception_type",
    "result.json": "id task_name trial_name trial_uri task_id source task_checksum config agent_info agent_result verifier_result verifier_environment_mode exception_info started_at finished_at environment_setup agent_setup agent_execution verifier step_results",
    "evidence-manifest.json": "files privacy",
    "verifier-receipt.json": "passed valid error_type oracle native_verify",
    "runtime-contract.json": "source_revision source_sha256 runtime profile workload_profile arm case_sha256 case_id intervention verification_intervention external_search_loop model source effort verify_mode verification_engine required_tools agent_timeout_sec profile_scope",
    "verification.json": "inputs judgments root_requests root_outputs",
    "intervention.json": "kind when llm_call_id response_id receipt_prefix_length native native_sha256 effective effective_sha256",
    "observation-check.json": "observation_valid cache_complete whole_runtime_complete full_runtime_expansion_ready blockers run_id run_spec_sha256 source_revision source_sha256 trial_name task_name task_checksum handoff_arm handoff_case_sha256 tool_calls replay_status accounting source_reconciliation verification timing limits artifact_sha256",
    "call-events.json": "action actor_id actor_type block_reason blocked dispatch_mode entity_id entity_type event handler_count handler_error_count id level llm_attempt_id llm_call_id occurred_at payload payload_hash retention_class run_id schema_version session_id session_key status step_id task_id tool_call_id turn_id",
    "native.json": "attempt_id sequence case_id engine mock started_at valid correct expected_verdict error_type actual_charge_usd correlation observer_has_sink_failures finished_at native_receipts accounting duration_ms projected_branch verdict",
}
PRIVATE_NAMES = {"auth.json", ".env", "credentials.json", "config.toml"}
MACHINE_PATH = re.compile(
    r"(?:(?<![A-Za-z0-9])/(?:Users|home|root|tmp|private|opt|workspace|logs|app)/[^\s\"'<>;,)]*"
    r"|(?<![A-Za-z0-9])[A-Za-z]:[\\/][^\s\"'<>;,)]*|~/(?:[^\s\"'<>;,)]*))"
)
PUBLIC_PREFIX = "reports/e2e-validation/jev-verdict-20260924"
RUN_RECORD = "docs/eval/jev-verdict-publication-20260924.md"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path):
    return json.loads(path.read_text())


def encoded(value) -> bytes:
    return (
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    ).encode()


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded(value))


def scan(path: Path) -> None:
    text = path.read_text()
    patterns = dict(_PUBLIC_SCAN_PATTERNS)
    # Source code contains the public scanner's regex itself, not local paths.
    if path.suffix != ".py":
        patterns["machine_path"] = MACHINE_PATH
    findings = {name: len(pattern.findall(text)) for name, pattern in patterns.items()}
    if any(findings.values()):
        raise ValueError(f"public scan failed: {path.name}: {findings}")


def project(value, removed: list[str], pointer: str = "", source_name: str = ""):
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            location = pointer + "/" + key.replace("~", "~0").replace("/", "~1")
            if key in OMIT and not (
                key == "tool_calls" and isinstance(item, (int, float))
            ):
                removed.append(location)
            else:
                result[key] = project(item, removed, location, source_name)
        return result
    if isinstance(value, list):
        return [
            project(item, removed, f"{pointer}/{i}", source_name)
            for i, item in enumerate(value)
        ]
    if isinstance(value, str) and source_name and source_name != "run-spec.json":
        field = next(
            part for part in reversed(pointer.split("/")) if not part.isdecimal()
        )
        if not re.fullmatch(r"[a-f0-9]{64}", value):
            allowed = field in TEXT_FIELDS or source_name == "evidence-manifest.json"
            if not allowed or len(value) > 256:
                raise ValueError(f"unreviewed nested text: {source_name}: {pointer}")
    if isinstance(value, str) and MACHINE_PATH.search(value):
        removed.append(pointer + " (machine-path value masked)")
        return MACHINE_PATH.sub("[local-path-withheld]", value)
    return value


def source_label(path: Path, sources: Path) -> str:
    try:
        return path.relative_to(sources).as_posix()
    except ValueError:
        return "external/" + path.name


def publish_source(source: Path, output: Path, sources: Path, receipts: list) -> None:
    removed: list[str] = []
    if source.suffix == ".json":
        native = load(source)
        allowed = set(FIELDS[source.name].split())
        rows = native if isinstance(native, list) else [native]
        if any(not isinstance(row, dict) or set(row) - allowed for row in rows):
            raise ValueError(f"unreviewed top-level fields: {source.name}")
        public = project(native, removed, source_name=source.name)
    else:
        public = {
            "classification": "withheld-private",
            "source_sha256": digest(source),
            "source_bytes": source.stat().st_size,
            "reason": "Diagnostic transcript withheld; failure class is in attempts.jsonl.",
        }
        removed.append("entire text body")
    write(output, public)
    scan(output)
    receipts.append(
        {
            "source": source_label(source, sources),
            "source_sha256": digest(source),
            "source_bytes": source.stat().st_size,
            "public": output.as_posix(),
            "public_sha256": digest(output),
            "removed_fields": sorted(set(removed)),
        }
    )


def cohort(
    sources: Path, output: Path, name: str, timestamp: str, receipts: list
) -> dict:
    source = sources / COHORTS[name]
    target = output / name
    validate_run_bundle(source / "run-spec.json")
    spec = load(source / "run-spec.json")
    # Keep the frozen experiment contract as a separately identified source.
    publish_source(
        source / "run-spec.json", target / "source-contract.json", sources, receipts
    )
    native_results = load(source / "results.json")
    publish_source(source / "results.json", target / "results.json", sources, receipts)
    attempts = [
        json.loads(line)
        for line in (source / "attempts.jsonl").read_text().splitlines()
    ]
    analysis = load(source / "analysis.json")
    refs = {r["path"] for a in attempts for r in a["evidence_refs"]}
    refs.update(r["path"] for r in analysis["evidence_refs"])
    refs.update(a["error_ref"] for a in attempts if a["error_ref"])
    paths = {
        relative: relative
        if relative.endswith(".json")
        else relative + ".withheld.json"
        for relative in refs
    }
    for relative in sorted(refs - {"results.json"}):
        publish_source(source / relative, target / paths[relative], sources, receipts)
    for row in attempts:
        row["change"]["description"] += (
            " Public retrospective projection; native bytes retained privately."
        )
        for ref in row["evidence_refs"]:
            ref["path"] = paths[ref["path"]]
            ref["sha256"] = digest(target / ref["path"])
        if row["error_ref"]:
            row["error_ref"] = paths[row["error_ref"]]
    attempts = project(attempts, [])
    target.joinpath("attempts.jsonl").write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n"
            for row in attempts
        )
    )
    receipts.append(
        {
            "source": source_label(source / "attempts.jsonl", sources),
            "source_sha256": digest(source / "attempts.jsonl"),
            "source_bytes": (source / "attempts.jsonl").stat().st_size,
            "public": (target / "attempts.jsonl").as_posix(),
            "public_sha256": digest(target / "attempts.jsonl"),
            "removed_fields": [],
            "changes": ["public evidence digests", "projection disclosure"],
        }
    )
    spec["created_at"] = timestamp
    spec["preregistration"] = {
        "mode": "retrospective",
        "status": "frozen",
        "frozen_at": timestamp,
        "live_test_approved": False,
        "operator": "public projection; no new execution",
    }
    spec["study"]["analysis_plan"] += (
        " Retrospective disclosure only; original prospective contract is source-contract.json."
    )
    spec["privacy"] = {
        "classification": "public",
        "redaction_boundary": "Reviewed file/field projection; private prompts, reasoning and machine paths withheld.",
    }
    spec["reproduction"]["comparison"]["promotion_authority"] = "none"
    write(target / "run-spec.json", spec)
    analysis["analyzed_at"] = timestamp
    analysis["run_spec_sha256"] = digest(target / "run-spec.json")
    analysis["attempts_sha256"] = digest(target / "attempts.jsonl")
    analysis["limitations"].append(
        "Retrospective public projection. Original contracts, receipts and digests remain separate; no new model calls."
    )
    for ref in analysis["evidence_refs"]:
        ref["path"] = paths[ref["path"]]
        ref["sha256"] = digest(target / ref["path"])
    write(target / "analysis.json", analysis)
    for filename in ("run-spec.json", "analysis.json"):
        receipts.append(
            {
                "source": source_label(source / filename, sources),
                "source_sha256": digest(source / filename),
                "source_bytes": (source / filename).stat().st_size,
                "public": (target / filename).as_posix(),
                "public_sha256": digest(target / filename),
                "removed_fields": [],
                "changes": ["retrospective public projection and references"],
            }
        )
    for trial in sorted((source / "trials").glob("*")):
        for relative in (
            "verifier/verifier-receipt.json",
            "agent/runtime-contract.json",
            "agent/verification.json",
            "agent/intervention.json",
            "observation-check.json",
        ):
            if (trial / relative).is_file():
                publish_source(
                    trial / relative,
                    target / "trials" / trial.name / relative,
                    sources,
                    receipts,
                )
    validate_run_bundle(target / "run-spec.json")
    return {
        "cohort": name,
        "source_run_id": load(source / "run-spec.json")["run_id"],
        "source_revision": spec["reproduction"]["geode"]["revision"],
        "source_contract_sha256": digest(source / "run-spec.json"),
        "source_results_sha256": digest(source / "results.json"),
        "source_attempts_sha256": digest(source / "attempts.jsonl"),
        "primary": native_results["primary"],
        "actual_attempts": sum(
            not a["attempt_id"].endswith("aggregate") for a in attempts
        ),
        "aggregate_rows_not_rollouts": sum(
            a["attempt_id"].endswith("aggregate") for a in attempts
        ),
        "validity": "invalid" if name.startswith("invalid/") else "valid",
        "kind": "component-diagnostic"
        if name == "snapshots"
        else "admission"
        if name.startswith("admission/")
        else "rollout-diagnostic",
        "promotion_authority": "none",
    }


def trajectories(sources: Path, repository: Path, name: str, timestamp: str) -> dict:
    root = sources / COHORTS[name]
    values, originals = {}, {}
    for path in sorted((root / "trials").glob("*/agent/geode-trajectory.json")):
        trial = path.parent.parent.name
        value = load(path)
        verify_trajectory_integrity(value)
        value["privacy"] = {
            "review_state": "reviewed",
            "payloads": "Existing content digests retained",
            "review_method": "Field allowlist, secret/identity scan, source integrity reconciliation",
            "license_status": "Authored synthetic diagnostic; no third-party task dataset",
        }
        value["provenance"] = {
            **value["provenance"],
            "public_transform": "normalize.py; metadata-only publication derivation",
            "source_revision": load(root / "run-spec.json")["reproduction"]["geode"][
                "revision"
            ],
        }
        value["artifact_digests"] = []
        for origin in (
            path,
            path.parent.parent / "result.json",
            path.parent.parent / "verifier/verifier-receipt.json",
        ):
            ref = f"{name}/{trial}/{origin.parent.name}-{origin.name}"
            value["artifact_digests"].append({"path": ref, "sha256": digest(origin)})
            originals[ref] = origin
        values[trial + ".json"] = value
    scope = f"jev-verdict-{name}-20260924"
    review = {
        "reviewer": "GEODE public evidence review",
        "reviewed_at": timestamp,
        "method": "Allowlisted digest projections and structural/secret/identity review",
        "scope": scope,
        "attestation": "Only the existing digest-projected events and reviewed provenance metadata are admitted; no prompts, hidden reasoning or raw tool bodies.",
    }
    existing = list((repository / "trajectories").glob(f"geode-jev-{scope}-*"))
    if existing:
        if len(existing) != 1:
            raise ValueError("ambiguous prepared trajectory release")
        release = existing[0]
        # Replay the deterministic projection comparison before reusing prepared bytes.
        for filename, value in values.items():
            if load(release / filename) != value:
                raise ValueError(
                    "prepared release differs; preserve it and choose a new publication timestamp"
                )
    else:
        release = stage_trajectory_release(
            repository / "trajectories",
            release_source="geode-jev",
            release_scope=scope,
            trajectories=values,
            published_at=timestamp,
            require_complete=False,
            privacy_review=review,
            source_artifacts=originals,
        )
    manifest = release / "manifest.json"
    verified = verify_trajectory_release(
        release, expected_manifest_sha256=digest(manifest)
    )
    for p in release.iterdir():
        scan(p)
    return {
        "cohort": name,
        "path": release.relative_to(repository).as_posix(),
        "manifest_sha256": digest(manifest),
        "quality": verified["quality"],
    }


def archive_rebound(sources: Path) -> dict:
    rows, checks = [], []
    for name, relative in COHORTS.items():
        root = sources / relative
        freeze = load(root / "freeze.json")
        missing = []
        for original, expected in freeze["sha256"].items():
            path = Path(original)
            if not path.is_absolute():
                path = root / path
            if path.name in PRIVATE_NAMES or "private-secrets" in path.parts:
                raise ValueError(
                    "credential reference is not admissible for content review"
                )
            if path.is_file():
                if digest(path) != expected:
                    raise ValueError("frozen source changed")
                continue
            missing.append((original, expected))
        if missing:
            archive = Path(freeze["source_bundle"])
            if digest(archive) != freeze["source_sha256"]:
                raise ValueError("archive identity mismatch")
            with tarfile.open(archive) as bundle:
                for original, expected in missing:
                    matches = [
                        member
                        for member in bundle.getmembers()
                        if member.isfile() and original.endswith("/" + member.name)
                    ]
                    if len(matches) != 1:
                        raise ValueError(
                            "missing source does not identify one archive member"
                        )
                    member = matches[0]
                    stream = bundle.extractfile(member)
                    if (
                        stream is None
                        or hashlib.sha256(stream.read()).hexdigest() != expected
                    ):
                        raise ValueError(
                            "missing source not recovered by pinned archive member"
                        )
                    rows.append(
                        {
                            "cohort": name,
                            "original_location": "retired-worktree/" + member.name,
                            "archive": source_label(archive, sources),
                            "archive_sha256": digest(archive),
                            "member": member.name,
                            "member_sha256": expected,
                            "matches_frozen_sha256": True,
                        }
                    )
        checks.append(
            {
                "cohort": name,
                "frozen_refs": len(freeze["sha256"]),
                "direct_matches": len(freeze["sha256"]) - len(missing),
                "archive_member_matches": len(missing),
                "changed": 0,
            }
        )
    return {"rebound": rows, "checks": checks}


def judgment_timing(sources: Path, output: Path, receipts: list) -> None:
    source = sources / "jev-verdict-20260923-r2/analysis-review/natural-audit.json"
    audit = load(source)
    rows = []
    for trial_index, trial in enumerate(audit["trials"]):
        calls = [
            (i, call)
            for i, call in enumerate(trial["call_sequence"])
            if call["purpose"] == "turn_verification"
        ]
        if len(calls) != 1:
            raise ValueError(
                "expected exactly one final-verdict call per natural trial"
            )
        call_index, call = calls[0]
        root = sources / COHORTS["natural"] / "trials" / trial["trial_name"]
        events_path = root / "agent/call-events.json"
        receipt_path = root / "trial-receipt.json"
        if digest(events_path) != trial["source_hashes"]["agent/call-events.json"]:
            raise ValueError("audit call-event source identity mismatch")
        if digest(receipt_path) != trial["source_hashes"]["trial-receipt.json"]:
            raise ValueError("audit runtime receipt identity mismatch")
        events = [
            (i, event)
            for i, event in enumerate(load(events_path))
            if event["id"] == call["source_event_id"]
        ]
        if len(events) != 1:
            raise ValueError("judge event identity is not unique")
        event_index, event = events[0]
        payload = event["payload"]
        if (
            event["action"] != "llm.call.ended"
            or payload["purpose"] != "turn_verification"
            or event["payload_hash"] != call["source_payload_sha256"]
            or payload["duration_ms"] / 1000 != call["duration_seconds"]
            or payload["model"] != call["model"]
            or load(receipt_path)["runtime"]["elapsed_seconds"]
            != trial["runtime_seconds"]
        ):
            raise ValueError("audit timing differs from native call or runtime receipt")
        rows.append(
            {
                "trial_name": trial["trial_name"],
                "case_id": trial["case_id"],
                "repetition": trial["repetition"],
                "arm": trial["arm"],
                "engine": trial["engine"],
                "model": payload["model"],
                "purpose": payload["purpose"],
                "source": payload["source"],
                "effort": payload["effort"],
                "llm_call_id": payload["llm_call_id"],
                "llm_attempt_id": event["llm_attempt_id"],
                "duration_ms": payload["duration_ms"],
                "duration_seconds": call["duration_seconds"],
                "runtime_seconds": trial["runtime_seconds"],
                "audit_pointer": f"/trials/{trial_index}/call_sequence/{call_index}",
                "native_event": {
                    "source": source_label(events_path, sources),
                    "sha256": digest(events_path),
                    "event_id": event["id"],
                    "payload_sha256": event["payload_hash"],
                    "duration_pointer": f"/{event_index}/payload/duration_ms",
                },
                "native_runtime": {
                    "source": source_label(receipt_path, sources),
                    "sha256": digest(receipt_path),
                    "duration_pointer": "/runtime/elapsed_seconds",
                },
            }
        )
    if len(rows) != 12 or any(
        sum(row["arm"] == arm for row in rows) != 6 for arm in ("a", "b")
    ):
        raise ValueError("natural judgment timing denominator changed")
    medians = {
        arm: {
            field: statistics.median(row[field] for row in rows if row["arm"] == arm)
            for field in ("duration_seconds", "runtime_seconds")
        }
        for arm in ("a", "b")
    }
    target = output / "natural/judgment-timing.json"
    write(
        target,
        {
            "scope": "M4 natural cohort; descriptive arm medians, not causal effects or a median of paired ratios",
            "audit_source": {
                "source": source_label(source, sources),
                "sha256": digest(source),
            },
            "rows": rows,
            "arm_medians": medians,
            "judge_response_median_ratio_a_over_b": medians["a"]["duration_seconds"]
            / medians["b"]["duration_seconds"],
            "runtime_median_relative_reduction_b_vs_a": 1
            - medians["b"]["runtime_seconds"] / medians["a"]["runtime_seconds"],
            "duration_authority": "Native llm.call.ended payload.duration_ms divided by 1000; not native_verify.duration_ms or replay timing",
            "actual_charge_usd": None,
        },
    )
    scan(target)
    receipts.append(
        {
            "source": source_label(source, sources),
            "source_sha256": digest(source),
            "source_bytes": source.stat().st_size,
            "public": target.as_posix(),
            "public_sha256": digest(target),
            "removed_fields": [
                "all audit fields except the 12 selected timing/correlation/source fields"
            ],
            "changes": [
                "native duration and source-hash reconciliation",
                "recomputed descriptive medians",
            ],
        }
    )


def prepare(args) -> None:
    sources, repository = args.sources.resolve(), args.repository.resolve()
    output = repository / PUBLIC_PREFIX
    if (
        sources == repository
        or sources in repository.parents
        or repository in sources.parents
    ):
        raise ValueError("private sources and public repository must be separate trees")
    frozen_sources = archive_rebound(sources)
    receipts = []
    lineage = [
        cohort(sources, output, name, args.prepared_at, receipts) for name in COHORTS
    ]
    judgment_timing(sources, output, receipts)
    releases = [
        trajectories(sources, repository, name, args.prepared_at)
        for name in ("natural", "recovery")
    ]
    for row in receipts:
        row["public"] = Path(row["public"]).relative_to(output).as_posix()
    inventory = []
    inventory_paths: set[Path] = set()
    for relative in COHORTS.values():
        root = sources / relative
        inventory_paths.update(root.rglob("*"))
    run_roots = {sources / relative.split("/")[0] for relative in COHORTS.values()}
    for root in run_roots:
        inventory_paths.update(root.glob("*"))
        for directory in (
            "payloads",
            "task-bundle",
            "infrastructure",
            "setup-preflight",
            "analysis-review",
        ):
            inventory_paths.update((root / directory).rglob("*"))
    credential_exclusions = [
        {
            "source": source_label(root / "private-secrets", sources),
            "classification": "private-secret",
            "bytes_read": 0,
            "reason": "Credential directory excluded without reading or hashing its files.",
        }
        for root in sorted(run_roots)
        if (root / "private-secrets").is_dir()
    ]
    for path in sorted(inventory_paths):
        if (
            not path.is_file()
            or "presentation" in path.parts
            or "self-check" in str(path)
        ):
            continue
        if path.name in PRIVATE_NAMES or path.name.startswith(".env."):
            raise ValueError(
                "credential-named file found; no bytes read, admission review required"
            )
        inventory.append(
            {
                "source": source_label(path, sources),
                "bytes": path.stat().st_size,
                "sha256": digest(path),
                "classification": "withheld-private",
                "reason": "Immutable source. Only separately named public projections are included.",
            }
        )
    private_root = sources / "jev-verdict-publication-20260924"
    private_manifest = private_root / "private-admission-manifest.json"
    private_value = {
        "schema": "geode.eval-artifact-publication.v1",
        "run_id": "jev-verdict-private-admission-20260924",
        "artifact_repository": {
            "url": "https://github.com/mangowhoiscloud/geode-eval-artifacts",
            "base_revision": args.base_revision,
            "destination_prefix": PUBLIC_PREFIX,
        },
        "geode": {
            "repository": "https://github.com/mangowhoiscloud/geode",
            "revision": args.geode_revision,
            "run_record": "docs/eval/typesafe-decision-handoff.md",
        },
        "publication": {
            "status": "prepared",
            "artifact_merge_revision": None,
            "published_at": None,
        },
        "verification": {
            "local_identity_scrubbed": False,
            "secret_scan_passed": False,
            "source_hashes_verified": True,
        },
        "entries": [
            {
                "classification": row["classification"],
                "bytes": row["bytes"],
                "sha256": row["sha256"],
                "local_path": ".geode/eval-runs/" + row["source"],
                "remote_path": None,
                "reason": row["reason"],
            }
            for row in inventory
        ],
        "notes": {
            "purpose": "Private source admission only. Contains no approved public bytes.",
            "credential_exclusions": credential_exclusions,
        },
    }
    write(private_manifest, private_value)
    original_geode = sources.parent.parent
    subprocess.run(
        [
            sys.executable,
            "-B",
            str(original_geode / "scripts/eval/contract.py"),
            "validate-publication",
            str(private_manifest),
        ],
        check=True,
        cwd=original_geode,
        env={**os.environ, "PYTHONPATH": str(original_geode)},
    )
    write(
        output / "normalization-receipt.json",
        {
            "prepared_at": args.prepared_at,
            "normalizer_sha256": digest(Path(__file__)),
            "geode_normalizer_revision": args.geode_revision,
            "geode_normalizer_source_files": {
                relative: digest(
                    Path(sys.modules[validate_run_bundle.__module__].__file__)
                    .resolve()
                    .parents[2]
                    / relative
                )
                for relative in (
                    "core/observability/trajectory.py",
                    "core/observability/trajectory_release.py",
                    "core/observability/redaction.py",
                    "scripts/eval/contract.py",
                )
            },
            "implementation_identity_note": "The supplied Git revision does not by itself attest a clean worktree; the exact publication-owner source bytes are bound above.",
            "native_sources_modified": False,
            "model_calls": 0,
            "source_public_mappings": receipts,
            "archive_member_rebound": frozen_sources["rebound"],
            "frozen_source_validation": frozen_sources["checks"],
            "withheld_inventory": inventory,
            "credential_exclusions": credential_exclusions,
            "private_admission_manifest": {
                "source": source_label(private_manifest, sources),
                "sha256": digest(private_manifest),
                "entries": len(inventory),
            },
            "trajectory_releases": releases,
        },
    )
    write(
        output / "lineage.json",
        {
            "cohorts": lineage,
            "pooled_primary": None,
            "replacement_edges": [
                ["invalid/collector", "admission/natural"],
                ["invalid/recovery-original", "invalid/recovery-r2"],
                ["invalid/recovery-r2", "recovery"],
            ],
            "admission_reuse": {"recovery": "admission/recovery"},
            "unexecuted_cells": {
                "invalid/collector": 1,
                "invalid/recovery-original": 3,
                "invalid/recovery-r2": 3,
            },
            "historical_predecessors": "Earlier r6 observations are not current evidence; M4 frozen source binds the prior r6 results digest.",
            "aggregate_rows": "Bookkeeping rows, never extra model calls or rollouts.",
        },
    )
    # This directory's manifest owns only its own files. Trajectories have their
    # existing independent manifests and are bound above, without duplicate copies.
    entries = []
    for path in sorted(output.rglob("*")):
        if not path.is_file() or path.name == "publication-manifest.json":
            continue
        scan(path)
        entries.append(
            {
                "classification": "public",
                "local_path": path.relative_to(output).as_posix(),
                "remote_path": path.relative_to(repository).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": digest(path),
            }
        )
    manifest = {
        "schema": "geode.eval-artifact-publication.v1",
        "run_id": "jev-verdict-publication-20260924",
        "artifact_repository": {
            "url": "https://github.com/mangowhoiscloud/geode-eval-artifacts",
            "base_revision": args.base_revision,
            "destination_prefix": PUBLIC_PREFIX,
        },
        "geode": {
            "repository": "https://github.com/mangowhoiscloud/geode",
            "revision": args.geode_revision,
            "run_record": RUN_RECORD,
        },
        "publication": {
            "status": "prepared",
            "artifact_merge_revision": None,
            "published_at": None,
        },
        "verification": {
            "local_identity_scrubbed": True,
            "secret_scan_passed": True,
            "source_hashes_verified": True,
        },
        "entries": entries,
        "notes": {
            "scope": "Reviewed public projections, not original raw bytes or training-ready data",
            "withheld_inventory": "normalization-receipt.json#/withheld_inventory",
            "trajectory_releases": releases,
            "normalizer": {"path": "normalize.py", "sha256": digest(Path(__file__))},
            "remote_readback": "Not performed; parent review and PR required.",
        },
    }
    write(output / "publication-manifest.json", manifest)
    scan(output / "publication-manifest.json")
    validate_publication(output / "publication-manifest.json")
    print(
        json.dumps(
            {
                "status": "prepared",
                "bundles": len(COHORTS),
                "public_report_files": len(entries),
                "trajectory_releases": [r["path"] for r in releases],
                "model_calls": 0,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--prepared-at", required=True)
    parser.add_argument("--base-revision", required=True)
    parser.add_argument("--geode-revision", required=True)
    prepare(parser.parse_args())
