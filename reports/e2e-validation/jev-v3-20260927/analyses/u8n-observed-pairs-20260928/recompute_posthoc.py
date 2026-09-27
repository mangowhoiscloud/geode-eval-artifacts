#!/usr/bin/env python3
"""Recompute the disclosed final candidates; no model calls or native run access."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_line(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode()


def relative_file(root: Path, name: str) -> Path:
    rel = Path(name)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError("only public relative file references are admitted")
    path = (root / rel).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError("public reference is absent or outside the report")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True,
                        help="published Jev report root containing evidence/")
    parser.add_argument("--source", type=Path, required=True,
                        help="GEODE source checkout with the map-pinned scoring owners")
    parser.add_argument("--map", type=Path, default=Path(__file__).with_name("public-state-map.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("refusing to overwrite an existing reproduction")
    manifest = json.loads(args.map.read_text())
    data_path = relative_file(args.map.parent, manifest["data_file"])
    if sha(data_path) != manifest["data_sha256"]:
        raise ValueError("disclosed data SHA mismatch")
    for name, expected in manifest["scoring_owner_sha256"].items():
        if sha(relative_file(args.source, name)) != expected:
            raise ValueError("scoring owner SHA mismatch: " + name)

    def offline_only(event: str, _args: object) -> None:
        if event in {"socket.connect", "socket.getaddrinfo", "subprocess.Popen", "os.system"}:
            raise RuntimeError("offline reproduction forbids networking and child processes")

    sys.addaudithook(offline_only)
    sys.path.insert(0, str(args.source.resolve()))
    from evals.benchmarks import noul_conditions as noul
    if Path(noul.__file__).resolve() != (args.source / "evals/benchmarks/noul_conditions.py").resolve():
        raise ValueError("scoring module was shadowed by another checkout")

    map_path = relative_file(args.report, manifest["public_e8_map_ref"])
    if sha(map_path) != manifest["public_e8_map_sha256"]:
        raise ValueError("public E8 map SHA mismatch")
    public_map = json.loads(map_path.read_text())
    public_entries = {e["public_path"]: e for e in public_map["entries"] if e["public_path"]}
    consumed = {}

    def load_public(name: str, expected: str | None = None) -> dict:
        path = relative_file(args.report, name)
        digest = sha(path)
        if digest != public_entries[name]["public_sha256"] or (expected and digest != expected):
            raise ValueError("public evidence SHA mismatch: " + name)
        consumed[name] = digest
        return json.loads(path.read_text())

    results_ref = "evidence/e2e/jev-verdict-e2e-r8/u8n/results.json"
    results = load_public(results_ref)
    trials = {}
    grouped = defaultdict(dict)
    for item in results["trials"]:
        name = item["trial_name"]
        receipt = load_public(f"evidence/e2e/jev-verdict-e2e-r8/u8n/trials/{name}/trial-receipt.json")
        trials[name] = receipt
        key = (receipt["workload_id"], receipt["repetition"])
        engine = receipt["verification_engine"]
        if engine in grouped[key]:
            raise ValueError("duplicate arm in a public pair")
        grouped[key][engine] = receipt
    selected = {t["trial_name"] for arms in grouped.values()
                if set(arms) == {"llm", "jev"} and all(t["validity"] == "valid" for t in arms.values())
                for t in arms.values()}
    rows = [json.loads(line) for line in data_path.read_text().splitlines() if line.strip()]
    if len(rows) != 22 or {r["trial_name"] for r in rows} != selected:
        raise ValueError("disclosure does not cover exactly the 11 eligible public pairs")
    outputs = []
    counts = Counter()
    conditions = Counter()
    clusters = Counter()
    for index, row in enumerate(rows):
        entry = manifest["entries"][index]
        if entry["public_row_index"] != index or entry["trial_name"] != row["trial_name"]:
            raise ValueError("row/map ordering mismatch")
        if hashlib.sha256(canonical_line(row)).hexdigest() != entry["public_row_sha256"]:
            raise ValueError("row SHA mismatch")
        payload = load_public(row["payload_ref"], row["payload_public_sha256"])
        receipt = load_public(row["trial_receipt_ref"], row["trial_receipt_public_sha256"])
        if receipt != trials[row["trial_name"]]:
            raise ValueError("trial receipt reference differs")
        verification = row["verification"]
        if set(verification) != {"inputs", "judgments"} or len(verification["inputs"]) != 1 or len(verification["judgments"]) != 1:
            raise ValueError("exactly one final state/judgment is required")
        state = verification["inputs"][0]["state"]
        if state["task_contract"] != noul.INBOX_SYSTEM or state["original_request"] != noul.inbox_request(payload["case"]["items"]):
            raise ValueError("state differs from the authored synthetic task")
        # Native implementation validates payload, state shape, candidate schema,
        # observed order statuses, call joins, and original state digests.
        score = noul.score_trial(verification, payload)
        final = score["judgments"][0]
        retained = receipt["noul_score"]["judgments"][-1]
        if final["llm_call_id"] != retained["llm_call_id"] or final["gold"] != retained["gold"] or final["correct"] != retained["correct"]:
            raise ValueError("recomputed final judgment differs from the retained summary")
        arm = row["arm"]
        metrics = receipt["semantic_metrics"]
        counts[arm + "_strict_success"] += metrics["strict_success"]
        counts[arm + "_recovered"] += metrics["recovered"]
        counts[arm + "_held_delivery"] += metrics["held_delivery"]
        if arm == "A":
            conditions[row["cell"]] += 1
            clusters[row["cluster_id"]] += 1
        gold = final["gold"]
        all_correct = (gold["measurable"] and not gold["has_contradiction"]
                       and not gold["missing_evidence"]
                       and len(gold["item_kinds"]) == len(payload["case"]["items"])
                       and set(gold["item_kinds"].values()) == {"correct"})
        counts[arm + "_recomputed_final_c0m0_all_items_correct"] += all_correct
        if arm == "B":
            counts["B_final_judgment_missing_true"] += final["boolean_projection"]["missing_evidence"]
        outputs.append({"trial_name": row["trial_name"], "arm": arm,
                        "cell": row["cell"], "cluster_id": row["cluster_id"],
                        "item_count": len(payload["case"]["items"]),
                        "recomputed_final_judgment": final,
                        "strict_success": metrics["strict_success"],
                        "recovered": metrics["recovered"],
                        "held_delivery": metrics["held_delivery"],
                        "termination_reason": receipt["runtime"]["termination_reason"]})
    output = {"status": "public-final-candidate-recomputation-matched",
              "scoring_code_revision": manifest["scoring_code_revision"],
              "data_sha256": sha(data_path), "map_sha256": sha(args.map),
              "eligible_pairs": len(selected) // 2, "condition_denominators": dict(conditions),
              "source_denominators": dict(clusters), "summary": dict(counts),
              "native_primary_unchanged": results["primary"],
              "posthoc_subset": True, "ci_or_ni_added": False,
              "results": outputs, "consumed_public_sha256": consumed,
              "native_run_files_read": False, "model_calls": 0, "network_calls": 0}
    with args.output.open("x") as stream:
        json.dump(output, stream, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({k: v for k, v in output.items() if k not in {"results", "consumed_public_sha256"}}, sort_keys=True))


if __name__ == "__main__":
    main()
