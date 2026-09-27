#!/usr/bin/env python3
"""Export reviewed Jev E/I native evidence, never execute or rescore it.

The input is the retained campaign directory; output is a fresh report root.
Only named evidence types and synthetic task files are read. Private directories,
provider transcripts, session stores and media are never opened. Native hashes
inside evidence remain references to native bytes, not public-file checksums.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

RUN_PREFIXES = ("jev-verdict-e2e", "jev-intent-harbor")
PRUNE = {"private-secrets", ".git", "__pycache__"}
ROOT_JSON = {"source-pin.json", "source-proof.json", "offline-check.json", "payload-manifest.json"}
ROOT_TEXT = {"runner.py", "paired_dispatch.py", "run_guards.py", "slot_guards.py", "slot_agent.py", "source_pin.py", "self_test.py", "make_tasks.py", "protocol.md"}
PHASE_JSON = {"run-spec.json", "run-spec.proposed.json", "run-spec.generated-original.json", "schedule.proposed.json", "analysis.json", "results.json", "freeze.json", "execution-receipt.json", "playback-check.json", "dispatch-lock.json"}
PHASE_JSONL = {"attempts.jsonl", "slots.jsonl", "trial-starts.jsonl"}
TRIAL_JSON = {"result.json", "config.json", "trial-receipt.json", "evidence-manifest.json", "cleanup-observation.json", "replay-check.json", "observation-check.json"}
AGENT_JSON = {"runtime-result.json", "runtime-metadata.json", "runtime-contract.json", "runtime-finalized.json", "handoff-result.json", "verification.json", "recording.receipt.json", "call-events.json"}
TASK_FILES = {"instruction.md", "task.toml", "requirements.txt", "Dockerfile", "handoff_runtime.py", "verify.py", "test.sh", "case.json", "manifest.json"}
WITHHELD_FIELDS = {
    "final_text", "tool_calls", "tool_definitions", "root_outputs", "root_requests", "inputs",
    "raw_answer", "raw_response", "response_body", "request_body", "rollout_details",
    "messages", "system_prompt", "prompt", "provider_reasoning", "reflection", "rationale",
    "original_request", "candidate_output", "task_contract",
    "exception_message", "exception_traceback", "traceback", "stdout", "stderr",
    "authorization", "api_key", "access_token", "refresh_token", "id_token", "password",
    "credentials", "environment_variables", "env", "extra_instructions", "option_e_salt",
}
ACCOUNT_KEY = re.compile(r"(?:account.*(?:fingerprint|(?:^|_)id$)|fingerprint|account_fp)", re.I)
ACCOUNT_LITERAL = re.compile(r"(?i)(?:fingerprint|account_fp)\s*(?:=|:)\s*[\"']([a-f0-9]{8,64})[\"']")
HOST_PATH = re.compile(r"(?:file://)?(?:/(?:Users|home)/|/private/(?:tmp|var)/|/var/folders/|/tmp/|/opt/homebrew/)[^\s\"'<>\]\[{}),;`]+")
EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
SECRET = re.compile(r"\b(?:gh[opsu]_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}|apikey_[A-Za-z0-9_-]{8,}|AKIA[0-9A-Z]{16})\b|\bBearer\s+[A-Za-z0-9._~+/=-]{12,}", re.I)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def dump(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, indent=2) + "\n").encode()


def classification(parts: tuple[str, ...]) -> str | None:
    """An explicit path allowlist; nothing under agent homes/artifact mirrors."""
    if len(parts) == 1:
        if parts[0] in ROOT_JSON or parts[0] == "labels.jsonl" or parts[0] == "e2e-slots.jsonl":
            return "native-json"
        if parts[0] in ROOT_TEXT:
            return "runner-source"
    if parts[0] == "payloads" and len(parts) == 2 and parts[-1].endswith(".json"):
        return "synthetic-input"
    if parts[0] == "task-bundle" and parts[-1] in TASK_FILES and len(parts) <= 4:
        return "synthetic-task"
    if len(parts) == 2 and (parts[-1] in PHASE_JSON or parts[-1] in PHASE_JSONL or parts[-1].startswith("unit-stop-")):
        return "native-json"
    if len(parts) == 4 and parts[1] == "trials" and parts[-1] in TRIAL_JSON:
        return "native-json"
    if len(parts) == 5 and parts[1] == "trials":
        if parts[-2] == "agent" and parts[-1] in AGENT_JSON:
            return "native-json"
        if parts[-2] == "verifier" and parts[-1] in {"verifier-receipt.json", "reward.txt"}:
            return "native-json" if parts[-1].endswith("json") else "native-reward"
    return None


def inventory(root: Path):
    for run in sorted(root.iterdir()):
        if not run.name.startswith(RUN_PREFIXES) or not run.is_dir() or run.is_symlink():
            continue
        for directory, dirs, files in os.walk(run, followlinks=False):
            base = Path(directory)
            for name in sorted(dirs[:]):
                path = base / name
                rel = path.relative_to(root).as_posix()
                if name in PRUNE or "DO-NOT-OPEN" in name or path.is_symlink():
                    dirs.remove(name)
                    yield path, rel, "alias" if path.is_symlink() else "excluded-directory"
            for name in sorted(files):
                path = base / name
                rel = path.relative_to(root).as_posix()
                if path.is_symlink():
                    yield path, rel, "alias"
                else:
                    yield path, rel, classification(path.relative_to(run).parts)


def load_json(raw: bytes, suffix: str):
    return [json.loads(line) for line in raw.splitlines() if line.strip()] if suffix == ".jsonl" else json.loads(raw)


def account_values(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if ACCOUNT_KEY.search(key) and isinstance(item, str) and len(item) >= 8:
                yield item
            yield from account_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from account_values(item)


class Projector:
    def __init__(self, root: Path, identities: list[str]):
        self.root = root
        self.identities = {value: f"anonymous-account-{index + 1:02d}" for index, value in enumerate(sorted(set(identities)))}

    def text(self, value: str) -> str:
        for identity, replacement in self.identities.items():
            value = value.replace(identity, replacement)
        value = value.replace(str(self.root) + "/", "source-runs/")
        value = HOST_PATH.sub(lambda m: "withheld-local-path-" + sha(m.group().encode())[:16], value)
        value = EMAIL.sub("withheld-email", value)
        if SECRET.search(value):
            raise ValueError("secret-like material encountered in allowlisted content; no matching value printed")
        return value

    def value(self, value, changes: list, pointer="", *, task=False):
        if isinstance(value, dict):
            out = {}
            for key, item in value.items():
                public_key = self.text(key)
                p = pointer + "/" + public_key.replace("~", "~0").replace("/", "~1")
                if key != public_key:
                    changes.append({"pointer": p, "operation": "key-path-or-identity-redacted", "source_key_sha256": sha(key.encode())})
                # Native analysis.decision rationale is an authored scientific
                # conclusion, not a provider's hidden reasoning transcript.
                authored_decision = pointer.endswith("/decision") and key in {"rationale", "reasoning", "reason"}
                reasoning_body = key == "reasoning" and not (
                    isinstance(item, str) and item in {"none", "minimal", "low", "medium", "high", "xhigh", "max"}
                )
                if not task and not authored_decision and (key in WITHHELD_FIELDS or reasoning_body or "credential" in key.lower() or "auth_token" in key.lower()):
                    changes.append({"pointer": p, "operation": "field-omitted", "reason": "private body, identity, environment or unused sealed-selection metadata", "source_value_sha256": sha(dump(item))})
                    continue
                out[public_key] = self.value(item, changes, p, task=task)
            return out
        if isinstance(value, list):
            return [self.value(item, changes, pointer + "/" + str(i), task=task) for i, item in enumerate(value)]
        if isinstance(value, str):
            public = self.text(value)
            if public != value:
                changes.append({"pointer": pointer, "operation": "path-or-identity-redacted"})
            return public
        return value


def retained_scalars(source, public, path=""):
    """Every retained non-string scalar and ordered list cardinality must match."""
    count = 0
    if isinstance(public, dict):
        # Redacted path keys are separately byte-bound in the mapping.
        for key, value in public.items():
            if key in source:
                count += retained_scalars(source[key], value, path + "/" + key)
    elif isinstance(public, list):
        if len(source) != len(public):
            raise ValueError("list cardinality changed: " + path)
        for index, value in enumerate(public):
            count += retained_scalars(source[index], value, path + "/" + str(index))
    elif not isinstance(public, str):
        if type(source) is not type(public) or source != public:
            raise ValueError("numeric/bool/null evidence changed: " + path)
        count += 1
    return count


def exclusion_reason(rel: str) -> str:
    if "DO-NOT-OPEN" in rel or "private-secrets" in rel:
        return "sealed/secret directory: not traversed or read"
    if "/artifacts/logs/" in rel:
        return "duplicated native log export; canonical summaries published separately"
    if "/presentation/" in rel or Path(rel).suffix in {".mp4", ".png", ".gif", ".cast"}:
        return "media or raw replay transcript; separate media publication scope"
    if "e2e-sources.json" in rel:
        return "upstream sealed-source inventory includes unused spare identities; consumed synthetic tasks published instead"
    if Path(rel).suffix in {".gz", ".db", ".db-wal", ".db-shm", ".pid", ".lock"}:
        return "source archive, session store or transient runtime state; pinned revisions retained"
    if "/task-bundle/" in rel:
        return "unreviewed task-bundle file type"
    return "not in reviewed evidence allowlist: raw transcript, provider/event body, environment or incidental state"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="fresh report root (existing tools/docs permitted)")
    parser.add_argument("--plan", action="store_true", help="classify sizes only; do not read excluded content or write")
    args = parser.parse_args()
    root = args.input.resolve()
    entries = list(inventory(root))
    allowed = [(p, r, k) for p, r, k in entries if k not in {None, "alias", "excluded-directory"}]
    summary = {"lineages": len({r.split('/')[0] for _, r, _ in entries}), "source_files_selected": len(allowed), "source_bytes_selected": sum(p.stat().st_size for p, _, _ in allowed), "class_counts": dict(Counter(k for _, _, k in allowed)), "excluded_entries": len(entries) - len(allowed)}
    if args.plan:
        print(json.dumps(summary, sort_keys=True))
        return
    destination = args.output / "evidence/e2e"
    mapping_path = args.output / "evidence/e2e-source-map.json"
    if destination.exists() or mapping_path.exists():
        raise FileExistsError("refusing to overwrite an existing E2E projection")
    identities = []
    sources = {}
    for path, rel, kind in allowed:
        raw = path.read_bytes()
        sources[rel] = (raw, sha(raw))
        if path.suffix in {".json", ".jsonl"}:
            identities.extend(account_values(load_json(raw, path.suffix)))
        else:
            identities.extend(ACCOUNT_LITERAL.findall(raw.decode()))
    projector = Projector(root, identities)
    records, prepared = [], []
    scalar_checks = 0
    for path, rel, kind in entries:
        record = {"source_path": projector.text(rel), "classification": kind or "excluded", "source_sha256": None, "public_path": None, "public_sha256": None, "changed_fields": []}
        if kind in {None, "excluded-directory"}:
            record["reason"] = exclusion_reason(rel)
            record["source_bytes"] = path.stat().st_size if kind is None else None
            record["content_read"] = False
        elif kind == "alias":
            target = Path(os.path.abspath(path.parent / os.readlink(path)))
            try:
                record["alias_of"] = projector.text(target.relative_to(root).as_posix())
            except ValueError:
                record["alias_of"] = projector.text(str(target))
            record["reason"] = "native alias, not a new execution or duplicate score; target lineage retained separately"
            record["content_read"] = False
        else:
            raw, original_sha = sources[rel]
            changes = record["changed_fields"]
            if path.suffix in {".json", ".jsonl"}:
                native = load_json(raw, path.suffix)
                public = projector.value(native, changes, task=kind.startswith("synthetic"))
                scalar_checks += retained_scalars(native, public)
                data = b"".join((json.dumps(row, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n").encode() for row in public) if path.suffix == ".jsonl" else dump(public)
            else:
                data = projector.text(raw.decode()).encode()
                if data != raw:
                    changes.append({"pointer": "", "operation": "text-path-or-identity-redacted"})
            public_rel = "evidence/e2e/" + rel
            record.update(source_sha256=original_sha, source_bytes=len(raw), public_path=public_rel, public_sha256=sha(data), public_bytes=len(data), content_read=True, byte_identical=raw == data)
            prepared.append((path, args.output / public_rel, data, original_sha))
        records.append(record)
    # Check all originals again before any public writes.
    if any(sha(path.read_bytes()) != digest for path, _, _, digest in prepared):
        raise ValueError("source changed during projection")
    for _, output, data, _ in prepared:
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("xb") as stream:
            stream.write(data)
    public_ok = all(sha(output.read_bytes()) == sha(data) for _, output, data, _ in prepared)
    originals_ok = all(sha(path.read_bytes()) == digest for path, _, _, digest in prepared)
    if not public_ok or not originals_ok:
        raise ValueError("post-write hash verification failed")
    manifest = {
        "schema": "jev-v3.e2e-public-projection@1", "created_at": datetime.now(timezone.utc).isoformat(),
        "source_root_alias": "source-runs", "generator": "tools/export_e2e.py",
        "generator_sha256": sha(Path(__file__).read_bytes()), "summary": {**summary, "public_bytes": sum(len(data) for _, _, data, _ in prepared)},
        "authority": "Native embedded hashes bind retained original bytes; public_sha256 binds this transformed disclosure. No rescoring, retiming, attempted-cell filtering or pooled retry score.",
        "verification": {"original_selected_hashes_unchanged": originals_ok, "public_hashes_match": public_ok, "retained_numeric_bool_null_scalars_equal": scalar_checks, "ordered_list_cardinality_preserved": True},
        "identity_policy": "Account identifiers replaced consistently; host paths removed. Container paths in reviewed reproducibility code are retained. No account credential source is opened.",
        "entries": records,
    }
    mapping_path.parent.mkdir(parents=True, exist_ok=True)
    with mapping_path.open("xb") as stream:
        stream.write(dump(manifest))
    print(json.dumps({**manifest["summary"], "verification": manifest["verification"], "source_map_sha256": sha(mapping_path.read_bytes())}, sort_keys=True))


if __name__ == "__main__":
    main()
