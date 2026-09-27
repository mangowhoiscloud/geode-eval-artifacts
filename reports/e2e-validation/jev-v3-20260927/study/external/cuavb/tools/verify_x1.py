"""Model-free self-check for X1 and input-size statistics. Zero model or network calls.

1. Rebuild into a temporary directory and require byte-identical outputs.
2. Validate every state against GEODE's ``_VerificationState`` and bind the frozen
   workloads with ``verdict_panel_runner.workloads_from_states`` (state digests).
3. Freeze the dispatch order with ``verdict_panel.ordered_workload_ids``.
4. Measure each arm's exact wire input for the Choice question:
   - Astra: system prompt + ``<verification_input>`` + html-escaped ordered payload;
   - Jev: the SystemOne ``{state, questions, model}`` body.
   Token counts use tiktoken ``o200k_base`` (an OpenAI proxy; Jev's tokenizer is not
   public) beside chars/4.

Run with GEODE's uv environment and the ext-src checkout first on PYTHONPATH.
Writes ``out/length-stats.x1.json`` and ``out/workload-order.x1.json``.
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
FILES = ("states.x1.jsonl", "gold.x1.jsonl", "excluded.x1.jsonl", "reference.x1.jsonl")


def quantiles(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)

    def q(p: float) -> float:
        return ordered[min(len(ordered) - 1, int(p * (len(ordered) - 1) + 0.5))]

    return {
        "n": len(ordered),
        "min": ordered[0],
        "p10": q(0.10),
        "p50": q(0.50),
        "p90": q(0.90),
        "p95": q(0.95),
        "p99": q(0.99),
        "max": ordered[-1],
        "mean": round(sum(ordered) / len(ordered), 1),
        "sum": sum(ordered),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cache", type=Path, default=Path(os.environ.get("EXT_CACHE", ".")) / "cuavb"
    )
    args = parser.parse_args(argv)

    report: dict[str, Any] = {"checks": {}}
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            [sys.executable, str(HERE / "build_cuavb.py"), "--cache", str(args.cache),
             "--out", tmp],
            check=True,
            capture_output=True,
        )
        same = {
            name: (Path(tmp) / name).read_bytes() == (OUT / name).read_bytes()
            for name in (*FILES, "split-manifest.x1.json")
        }
    report["checks"]["rebuild_byte_identical"] = same

    from evals.benchmarks.decision_verification import (
        _LLM_SYSTEM_PROMPTS,
        _ordered,
        _VerificationState,
        base_questions,
        contract_digests,
    )
    from evals.benchmarks.typesafe_decision import JEV_MODEL
    from evals.benchmarks.verdict_panel import ordered_workload_ids
    from evals.benchmarks.verdict_panel_runner import workloads_from_states

    rows = [json.loads(line) for line in (OUT / "states.x1.jsonl").read_text().splitlines()]
    for row in rows:
        _VerificationState.model_validate(row["state"])
    manifest_sha = hashlib.sha256((OUT / "split-manifest.x1.json").read_bytes()).hexdigest()
    order = ordered_workload_ids([row["state_id"] for row in rows], manifest_sha)
    workloads = workloads_from_states(rows, order)
    report["checks"]["verification_state_valid"] = len(rows)
    report["checks"]["workloads_bound"] = len(workloads)
    gold_ids = [json.loads(x)["state_id"] for x in (OUT / "gold.x1.jsonl").read_text().splitlines()]
    report["checks"]["gold_covers_states_exactly"] = sorted(gold_ids) == sorted(order)

    import tiktoken

    encoding = tiktoken.get_encoding("o200k_base")
    questions = base_questions("choice")
    system_prompt = _LLM_SYSTEM_PROMPTS["choice"]
    e2e_chars, jev_chars, jev_tokens, llm_chars, llm_tokens = [], [], [], [], []
    per_state = []
    for row in rows:
        payload = {"state": row["state"], "questions": questions}
        jev_body = json.dumps({**payload, "model": JEV_MODEL}, ensure_ascii=False)
        llm_user = "<verification_input>" + escape(_ordered(payload)) + "</verification_input>"
        e2e = len(json.dumps(row["state"], ensure_ascii=False))
        jt = len(encoding.encode(jev_body))
        lt = len(encoding.encode(system_prompt)) + len(encoding.encode(llm_user))
        e2e_chars.append(e2e)
        jev_chars.append(len(jev_body))
        jev_tokens.append(jt)
        llm_chars.append(len(system_prompt) + len(llm_user))
        llm_tokens.append(lt)
        per_state.append(
            {"state_id": row["state_id"], "e2e_chars": e2e, "jev_o200k": jt, "astra_o200k": lt}
        )
    report["encoding"] = {"tokenizer": "tiktoken o200k_base", "tiktoken": tiktoken.__version__}
    report["contract_digests_choice"] = contract_digests("choice")
    report["state_e2e_chars"] = quantiles(e2e_chars)
    report["jev_body_chars"] = quantiles(jev_chars)
    report["jev_body_o200k_tokens"] = quantiles(jev_tokens)
    report["jev_body_chars_div4"] = quantiles([c / 4 for c in jev_chars])
    report["astra_input_chars"] = quantiles(llm_chars)
    report["astra_input_o200k_tokens"] = quantiles(llm_tokens)
    report["largest_states"] = sorted(per_state, key=lambda r: -r["e2e_chars"])[:5]
    report["over_bound"] = sum(value > 60_000 for value in e2e_chars)
    report["passed"] = (
        all(same.values())
        and report["checks"]["gold_covers_states_exactly"]
        and report["over_bound"] == 0
    )
    (OUT / "length-stats.x1.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    (OUT / "workload-order.x1.json").write_text(
        json.dumps(
            {
                "rule": "verdict_panel.ordered_workload_ids: ascending sha256(state_id + "
                "split-manifest sha256)",
                "split_manifest_sha256": manifest_sha,
                "ordered_workload_ids": order,
                "ordered_workload_ids_sha256": hashlib.sha256(
                    json.dumps(order, separators=(",", ":")).encode()
                ).hexdigest(),
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps({k: report[k] for k in ("checks", "over_bound", "passed")}, indent=1))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
