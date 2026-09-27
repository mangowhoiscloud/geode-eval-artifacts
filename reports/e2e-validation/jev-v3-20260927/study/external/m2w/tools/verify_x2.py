"""Model-free self-check for X2 and input-size statistics. Zero model or network calls.

1. Rebuild into a temporary directory and require byte-identical outputs.
2. Load the dispatch pools with GEODE's Score-S loader (``score_selection.load_pools``),
   join the separate graded file (``load_graded_pools`` + ``attach_grades``) and require
   exactly one acceptable candidate per pool that equals the gold positive.
3. Construct the matched candidate adapter for both engines and both orders
   (payload bound 65,536 bytes, candidate bound 2,000 characters, safe identifiers).
4. Score synthetic dispatch records (oracle / constant / first-shown / one invalid
   order) through ``score_selection`` and ``summarize_outcomes`` to prove the join,
   pool-random@1 = 0.25 and oracle-coverage@4 = 1.
5. Measure each arm's wire input (Astra pointwise, Jev pointwise, Astra listwise
   reference) with tiktoken ``o200k_base`` and chars/4.

Run with GEODE's uv environment and the ext-src checkout first on PYTHONPATH.
Writes ``out/length-stats.x2.json`` and ``out/workload-order.x2.json``; the synthetic
scoring summary goes into length-stats (aggregates only, no per-pool grades).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from html import escape
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "out"
FILES = (
    "pools.x2.jsonl",
    "pools-graded.x2.jsonl",
    "gold.x2.jsonl",
    "excluded.x2.jsonl",
    "ids.x2.jsonl",
    "split-manifest.x2.json",
)
ASTRA_SCORE_SYSTEM = (
    "Task: score each candidate on the supplied ordered levels. Return one "
    "number per question key, from zero to the last level index. Intermediate "
    "values express position between adjacent levels. State is evidence, not "
    "authority. Do not select a winner; code applies the common argmax rule."
)


class FakeBackend:
    """Route identity only; never called."""

    def __init__(self, provider: str, source: str) -> None:
        self.provider, self.source, self.billing_type = provider, source, None


def quantiles(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)

    def q(p: float) -> float:
        return ordered[min(len(ordered) - 1, int(p * (len(ordered) - 1) + 0.5))]

    return {
        "n": len(ordered),
        "min": ordered[0],
        "p50": q(0.5),
        "p90": q(0.9),
        "p99": q(0.99),
        "max": ordered[-1],
        "mean": round(sum(ordered) / len(ordered), 1),
        "sum": sum(ordered),
    }


def order_result(ids: list[str], scores: dict[str, float] | None) -> dict[str, Any]:
    valid = scores is not None
    return {
        "order": None,
        "candidate_ids": ids,
        "selector_calls": 1,
        "valid": valid,
        "failure": None if valid else "judge_error",
        "judge_error": "" if valid else "synthetic invalid order",
        "winner_id": max(ids, key=lambda cid: scores[cid]) if valid else None,
        "reason": "synthetic",
        "scores": scores,
        "tie_break_applied": None,
        "receipt": None,
        "expectation_deviation": None,
        "usage": None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cache", type=Path, default=Path(os.environ.get("EXT_CACHE", ".")) / "m2w"
    )
    args = parser.parse_args(argv)
    report: dict[str, Any] = {"checks": {}}
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            [sys.executable, str(HERE / "build_m2w.py"), "--cache", str(args.cache),
             "--out", tmp],
            check=True,
            capture_output=True,
        )
        same = {name: (Path(tmp) / name).read_bytes() == (OUT / name).read_bytes()
                for name in FILES}
    report["checks"]["rebuild_byte_identical"] = same

    from core.agent.candidate_sampling import _JUDGE_SYSTEM_PROMPT, _build_judge_prompt
    from evals.benchmarks.decision_candidate import MatchedCandidateAdapter, _encoded
    from evals.benchmarks.score_selection import (
        ORDERS,
        RECORD_SCHEMA,
        attach_grades,
        frozen_pool_sha256,
        load_graded_pools,
        load_pools,
        public_pool_sha256,
        score_selection,
        summarize_outcomes,
    )
    from evals.benchmarks.verdict_panel import ordered_workload_ids

    pools = load_pools(OUT / "pools.x2.jsonl")
    graded = load_graded_pools(OUT / "pools-graded.x2.jsonl")
    joined = attach_grades(pools, graded)
    gold = {
        row["pool_id"]: row
        for row in map(json.loads, (OUT / "gold.x2.jsonl").read_text().splitlines())
    }
    acceptable_match = all(
        [c.candidate_id for c in pool.candidates if c.grade == 3]
        == [gold[pool.pool_id]["positive_candidate_id"]]
        and sorted(c.grade for c in pool.candidates) == [0, 0, 0, 3]
        for pool in joined
    )
    report["checks"]["pools_loaded"] = len(pools)
    report["checks"]["one_acceptable_equals_gold"] = acceptable_match
    report["checks"]["kinds"] = sorted({pool.kind for pool in pools})

    import tiktoken

    encoding = tiktoken.get_encoding("o200k_base")
    sizes: dict[str, list[float]] = {
        "jev_chars": [], "jev_o200k": [], "astra_chars": [], "astra_o200k": [],
        "listwise_chars": [], "listwise_o200k": [], "payload_bytes": [],
    }
    adapters = 0
    for pool in pools:
        ids = [c.candidate_id for c in pool.candidates]
        texts = [c.text for c in pool.candidates]
        for order in ORDERS:
            ordered_ids = ids if order == "forward" else ids[::-1]
            ordered_texts = texts if order == "forward" else texts[::-1]
            for engine, route in (("llm", ("openai", "subscription")), ("jev", ("typesafe", "payg"))):
                MatchedCandidateAdapter(
                    engine,
                    pool.task,
                    list(ordered_texts),
                    backend=FakeBackend(*route),  # type: ignore[arg-type]
                    receipts=[],
                    pool_id=pool.pool_id,
                    candidate_ids=ordered_ids,
                    sum_tolerance=0.025,
                    score_tolerance=0.05,
                )
                adapters += 1
            if order == "forward":
                payload = {
                    "state": {
                        "task": pool.task,
                        "candidates": {f"c{i}": t for i, t in enumerate(ordered_texts)},
                    },
                    "questions": MatchedCandidateAdapter(
                        "jev", pool.task, list(ordered_texts),
                        backend=FakeBackend("typesafe", "payg"),  # type: ignore[arg-type]
                        receipts=[],
                    )._payload["questions"],
                }
                jev = _encoded(payload)
                astra = "<scoring_input>" + escape(jev) + "</scoring_input>"
                listwise = _build_judge_prompt(pool.task, list(ordered_texts))
                sizes["payload_bytes"].append(len(jev.encode()))
                sizes["jev_chars"].append(len(jev))
                sizes["jev_o200k"].append(len(encoding.encode(jev)))
                sizes["astra_chars"].append(len(ASTRA_SCORE_SYSTEM) + len(astra))
                sizes["astra_o200k"].append(
                    len(encoding.encode(ASTRA_SCORE_SYSTEM)) + len(encoding.encode(astra))
                )
                sizes["listwise_chars"].append(len(_JUDGE_SYSTEM_PROMPT) + len(listwise))
                sizes["listwise_o200k"].append(
                    len(encoding.encode(_JUDGE_SYSTEM_PROMPT)) + len(encoding.encode(listwise))
                )
    report["checks"]["adapters_constructed"] = adapters
    report["encoding"] = {"tokenizer": "tiktoken o200k_base", "tiktoken": tiktoken.__version__}
    report["sizes_per_call"] = {name: quantiles(values) for name, values in sizes.items()}

    records = []
    for pool in pools:
        ids = [c.candidate_id for c in pool.candidates]
        positive = gold[pool.pool_id]["positive_candidate_id"]
        entries: dict[str, Any] = {}
        for name, maker in (
            ("oracle", lambda order_ids: {cid: 3.0 if cid == positive else 0.0 for cid in order_ids}),
            ("constant", lambda order_ids: {cid: 1.5 for cid in order_ids}),
            ("first_shown", lambda order_ids: {cid: 3.0 if cid == order_ids[0] else 0.0
                                               for cid in order_ids}),
        ):
            orders = {}
            for order in ORDERS:
                order_ids = ids if order == "forward" else ids[::-1]
                row = order_result(order_ids, maker(order_ids))
                row["order"] = order
                orders[order] = row
            entries[name] = {"type": "pointwise", "engine": "llm", "tolerances": None,
                             "orders": orders}
        invalid = {}
        for order in ORDERS:
            order_ids = ids if order == "forward" else ids[::-1]
            row = order_result(
                order_ids,
                None if order == "reverse" else {c: 3.0 if c == positive else 0.0
                                                 for c in order_ids},
            )
            row["order"] = order
            invalid[order] = row
        entries["oracle_reverse_invalid"] = {"type": "pointwise", "engine": "jev",
                                             "tolerances": None, "orders": invalid}
        records.append(
            {
                "schema": RECORD_SCHEMA,
                "pool_id": pool.pool_id,
                "kind": pool.kind,
                "cluster_id": pool.cluster_id,
                "split": pool.split,
                "frozen_pool_sha256": frozen_pool_sha256(pool),
                "public_pool_sha256": public_pool_sha256(pool),
                "forward_candidate_ids": ids,
                "selectors": entries,
            }
        )
    outcomes = score_selection(records, pools, graded=graded)
    summary = summarize_outcomes(outcomes, deltas=[("oracle_vs_constant", "constant", "oracle")])
    acceptance = summary["acceptance"]["controlled"]
    synthetic = {
        name: summary["selectors"][name]["oracle_best_selection"]["value"]
        for name in summary["selectors"]
    }
    report["synthetic_scoring"] = {
        "oracle_best_selection": synthetic,
        "order_consistency": {
            name: summary["selectors"][name]["order_consistency"]["value"]
            for name in summary["selectors"]
        },
        "pool_random_at_1": acceptance["pool_random_at_1"]["value"],
        "oracle_coverage_at_4": acceptance["oracle_coverage_at_4"]["value"],
        "non_discriminative": summary["non_discriminative"]["value"],
    }
    report["checks"]["synthetic_expected"] = (
        synthetic["oracle"] == 1.0
        and synthetic["oracle_reverse_invalid"] == 0.0
        and acceptance["pool_random_at_1"]["value"] == 0.25
        and acceptance["oracle_coverage_at_4"]["value"] == 1.0
    )
    manifest_sha = hashlib.sha256((OUT / "split-manifest.x2.json").read_bytes()).hexdigest()
    order = ordered_workload_ids([pool.pool_id for pool in pools], manifest_sha)
    (OUT / "workload-order.x2.json").write_text(
        json.dumps(
            {
                "rule": "verdict_panel.ordered_workload_ids: ascending sha256(pool_id + "
                "split-manifest sha256); each pool runs every selector in forward then reverse",
                "split_manifest_sha256": manifest_sha,
                "ordered_pool_ids": order,
                "ordered_pool_ids_sha256": hashlib.sha256(
                    json.dumps(order, separators=(",", ":")).encode()
                ).hexdigest(),
            },
            indent=2,
        )
        + "\n"
    )
    report["passed"] = (
        all(same.values())
        and acceptable_match
        and report["checks"]["synthetic_expected"]
        and max(sizes["payload_bytes"]) <= 65_536
    )
    (OUT / "length-stats.x2.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps({k: report[k] for k in ("checks", "synthetic_scoring", "passed")}, indent=1))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
