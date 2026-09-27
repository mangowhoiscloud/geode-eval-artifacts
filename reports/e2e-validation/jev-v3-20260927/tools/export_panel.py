#!/usr/bin/env python3
"""Project operator-supplied Jev panel evidence; no models, network or rescoring.

Native digests remain source identities, never hashes of redacted public bytes.
Run with --verify-only to check a prepared public package without private input.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import statistics


OMIT = {
    "raw_answer", "response_id", "projected_payload", "reasoning_items",
    "reasoning_summaries", "chain_of_thought", "codex_output_items",
    "system_prompt", "messages", "authorization", "access_token", "refresh_token",
    "api_key", "codex_account_fp12", "expected_account_fp12", "account_id",
    "email", "auth_expiry_margin_s", "account_fingerprint", "account_fp12",
}
BODY_KEYS = {"reason", "reflection", "reflection_hint", "rationale", "summary"}
MACHINE_PATH = re.compile(
    r"(?:(?<![A-Za-z0-9])/(?:Users|home|root|tmp|private|opt|workspace|logs|app)/[^\s\"'<>;,)]*"
    r"|(?<![A-Za-z0-9])[A-Za-z]:[\\/][^\s\"'<>;,)]*|~/[^\s\"'<>;,)]*)"
)
EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
SECRET = re.compile(
    r"\b(?:gh[opsu]_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16})\b"
    r"|\bBearer\s+[A-Za-z0-9._~+/=-]{12,}\b"
    r"|[?&](?:api[_-]?key|access[_-]?token|token|secret)=[^&\s]{8,}", re.I
)
HOST = re.compile(r"jev-panel(?:-r[1-7])?\Z")
SAFE_NAMES = {
    "source-pin.json", "freeze.json", "run-spec.json", "run-spec.choice.json",
    "run-spec.noul.json", "execution-receipt.json", "execution-argument-refusal.json",
    "dispatch-summary.json", "dispatch-records.jsonl", "attempts.jsonl", "analysis.json",
    "results.json", "intent-results.json", "stability-results.json", "latency-results.json",
    "x1-results.json", "score-tolerance.json", "score-tolerance-freeze.json",
    "selection-freeze.json", "timings.json", "tolerance-check.json",
    "u0b-normalization.json", "u0b-controlled.normalized.jsonl",
    "u2s-paraphrase-normalization.json", "u2s-paraphrases.normalized.json",
    "pools.natural.jsonl", "generation-usage.jsonl", "heartbeat.jsonl",
    "pair-log.jsonl", "dispatch-log.jsonl",
}
SCIENCE_FIELDS = {
    "primary", "primary_metric", "confidence_interval", "interval_metrics",
    "headline", "outside", "engines", "outcomes", "items", "pairs", "strata",
    "decision", "hypothesis_status", "planned_families", "planned_items",
    "split_summary", "split_intervals", "discordant_counts", "judge_error_orders",
    "jev_accept_auroc_interval", "verdicts", "temperature_grid", "tau_grid",
    "temperatures", "cascade", "selection_metrics",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def dump(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


def load(path):
    text = path.read_text()
    return [json.loads(s) for s in text.splitlines() if s.strip()] if path.suffix == ".jsonl" else json.loads(text)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(dump(value))


def fingerprint_values(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if "fp12" in key or "fingerprint" in key:
                if isinstance(child, str) and re.fullmatch(r"[a-f0-9]{12}", child):
                    yield child
            yield from fingerprint_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from fingerprint_values(child)


def project(value, changes, fingerprints, *, model_body=False, pointer=""):
    if isinstance(value, dict):
        out = {}
        for key, child in value.items():
            loc = pointer + "/" + key.replace("~", "~0").replace("/", "~1")
            if key.lower() in OMIT or (model_body and key in BODY_KEYS):
                changes.append({"pointer": loc, "action": "removed", "reason": "private identity or unreviewed response/feedback body"})
                continue
            public_key = clean_text(key, fingerprints)
            if public_key != key:
                public_key += "#" + sha(key.encode())[:16]
                changes.append({"pointer": pointer, "action": "key-path-masked", "key_sha256": sha(key.encode())})
            if public_key in out:
                raise ValueError("redaction creates duplicate object key")
            out[public_key] = project(child, changes, fingerprints, model_body=model_body, pointer=loc)
        return out
    if isinstance(value, list):
        return [project(x, changes, fingerprints, model_body=model_body, pointer=f"{pointer}/{i}") for i, x in enumerate(value)]
    if isinstance(value, str):
        public = clean_text(value, fingerprints)
        if public != value:
            changes.append({"pointer": pointer, "action": "text-masked", "reason": "machine path, email, credential pattern or account fingerprint"})
        return public
    return value


def clean_text(value, fingerprints):
    value = MACHINE_PATH.sub("[local-path-withheld]", value)
    value = EMAIL.sub("[email-withheld]", value)
    value = SECRET.sub("[credential-withheld]", value)
    for fp in fingerprints:
        value = value.replace(fp, "[account-withheld]")
    return value


def classification(path):
    if path.suffix not in {".json", ".jsonl"}:
        return "excluded-implementation-cache-or-log"
    if path.name == "events.jsonl" or "sub_agents" in path.parts or "payloads" in path.parts:
        return "withheld-unreviewed-generation-event-or-response-body"
    if path.name in SAFE_NAMES or path.name.startswith("unit-stop-") or path.parent.name in {"receipts", "private-receipts"}:
        return "public-projection"
    raise ValueError(f"unreviewed research file: {path.name}")


def pointer(value, location):
    for part in location.lstrip("/").split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def verify(output):
    mapping = json.loads((output / "evidence/panel-source-map.json").read_text())
    checked = metrics = 0
    for row in mapping["files"]:
        if not row.get("public_path"):
            continue
        path = output / row["public_path"]
        data = path.read_bytes()
        assert sha(data) == row["public_sha256"], row["public_path"]
        assert not MACHINE_PATH.search(data.decode()), row["public_path"]
        assert not EMAIL.search(data.decode()), row["public_path"]
        assert not SECRET.search(data.decode()), row["public_path"]
        value = load(path)
        checked += 1
        if path.name == "analysis.json":
            for metric in value["metrics"]:
                locator = metric.get("source_locator")
                if not locator:
                    continue
                source = path.parent / metric["source_ref"]
                if not source.is_file():
                    raise ValueError(f"missing metric source: {source.name}")
                native = load(source)
                for field, loc in locator.items():
                    assert pointer(native, loc) == metric[field], (path.name, metric["name"], field)
                metrics += 1
    recomputed = []
    for rel in ["jev-panel-r5/u4/results.json", "jev-panel-r5/u5s/results.json", "jev-panel-r7/x2/results.json"]:
        data = load(output / "evidence/panel" / rel)
        rows = data["outcomes"]
        delta = sum(r["selectors"]["jev_pointwise"]["oracle_best_value"] - r["selectors"]["astra_pointwise"]["oracle_best_value"] for r in rows)
        assert delta == data["primary_metric"]["numerator"]
        assert len(rows) == data["primary_metric"]["denominator"]
        recomputed.append({"source": rel, "numerator": delta, "denominator": len(rows), "cluster_ids_present": all("cluster_id" in r for r in rows)})
    rel = "jev-panel-r4/u6a/choice/intent-results.json"
    data = load(output / "evidence/panel" / rel)
    delta = sum(int(r["jev"]["joint_correct"]) - int(r["llm"]["joint_correct"]) for r in data["items"])
    assert delta == data["primary"]["numerator"] and len(data["items"]) == data["primary"]["denominator"]
    recomputed.append({"source": rel, "numerator": delta, "denominator": len(data["items"])})
    rel = "jev-panel-r5/u3/choice/latency-results.json"
    data = load(output / "evidence/panel" / rel)
    pairs = [r for r in data["pairs"] if r["excluded_reason"] is None]
    median = statistics.median(r["delta_s"] for r in pairs)
    assert median == data["primary"]["value"]
    recomputed.append({"source": rel, "paired_median_delta_s": median, "pairs": len(pairs)})
    return {"public_files_verified": checked, "native_metric_locators_verified": metrics, "row_reaggregation": recomputed,
            "ci_policy": "Native CI bytes and seed/method retained; this check does not recompute bootstrap intervals or rescore model responses.",
            "privacy_scan": {"machine_paths": 0, "emails": 0, "credential_patterns": 0}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Private program directory containing jev-panel and r1-r7")
    parser.add_argument("--output", type=Path, required=True, help="Publication package directory")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.verify_only:
        print(json.dumps(verify(args.output), indent=2))
        return
    if args.input is None:
        parser.error("--input is required for projection")
    if (args.output / "evidence/panel-source-map.json").exists():
        raise ValueError("publication map already exists; use a new output directory")
    files = []
    omitted_links = []
    for host in sorted(args.input.iterdir()):
        if not host.is_dir() or not HOST.fullmatch(host.name):
            continue
        for path in sorted(host.rglob("*")):
            if any(part == "private-secrets" or part.endswith("DO-NOT-OPEN") for part in path.parts):
                continue
            if path.is_symlink():
                omitted_links.append(path.relative_to(args.input).as_posix())
                continue
            if path.is_file():
                files.append((path, classification(path)))
    fingerprints = set()
    for path, status in files:
        if status == "public-projection":
            fingerprints.update(fingerprint_values(load(path)))
    records = []
    preserved_science_fields = 0
    for path, status in files:
        raw = path.read_bytes()
        row = {"source_path": path.relative_to(args.input).as_posix(), "source_sha256": sha(raw), "source_bytes": len(raw), "classification": status}
        if status == "public-projection":
            value = load(path)
            changes = []
            is_model_body = path.parent.name == "receipts" or path.name == "dispatch-records.jsonl"
            public = project(value, changes, fingerprints, model_body=is_model_body)
            if isinstance(value, dict) and (path.name.endswith("results.json") or path.name in {"analysis.json", "selection-freeze.json"}):
                for key in SCIENCE_FIELDS & value.keys():
                    assert public[key] == value[key], (path.name, key, "scientific field changed")
                    preserved_science_fields += 1
            # These two inputs are authored synthetic inboxes/candidates, not external text.
            # External task bodies are not present in admitted RUN files; response bodies
            # are removed even when they echo a public or synthetic input.
            data = ("".join(json.dumps(r, ensure_ascii=False, allow_nan=False, separators=(",", ":")) + "\n" for r in public).encode()
                    if path.suffix == ".jsonl" else dump(public))
            public_path = Path("evidence/panel") / path.relative_to(args.input)
            destination = args.output / public_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            row.update(public_path=public_path.as_posix(), public_sha256=sha(data), public_bytes=len(data), byte_identical=raw == data,
                       changes=changes, source_digest_fields="retained source identities; use this map for public-file hashes")
        records.append(row)
        assert sha(path.read_bytes()) == row["source_sha256"], "source changed while exporting"
    # Change pointers can themselves contain private absolute-map keys.
    mapping = project({"schema": "jev-v3-panel-publication-map@1", "status": "prepared-not-published",
                       "source_root": "operator supplied --input (not published)", "exporter_sha256": sha(Path(__file__).read_bytes()),
                       "authority": "Public projections of native evidence; no new experiment, no native bundle validation claim.",
                       "symlinks_not_followed": omitted_links,
                       "classification_counts": dict(Counter(r["classification"] for r in records)), "files": records}, [], fingerprints)
    write(args.output / "evidence/panel-source-map.json", mapping)
    report = verify(args.output)
    report["source_files_sha_preserved"] = len(records)
    report["scientific_fields_exactly_equal_to_source"] = preserved_science_fields
    report["exporter_sha256"] = sha(Path(__file__).read_bytes())
    write(args.output / "evidence/panel/verification.json", report)
    print(json.dumps({"files": len(records), "public_files": report["public_files_verified"], "metrics": report["native_metric_locators_verified"]}))


if __name__ == "__main__":
    main()
