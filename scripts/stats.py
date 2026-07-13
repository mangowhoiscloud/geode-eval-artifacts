"""Recompute the README's quantitative summary from the artifacts themselves.

Run from the repository root: python3 scripts/stats.py
Every number in the README's "Quantitative summary" section comes from this
script; if the artifacts and the README disagree, trust this script and fix
the README.
"""

import glob
import json
from collections import Counter


def mcpmark() -> None:
    t = {"tasks": 0, "passed": 0, "input_tokens": 0, "output_tokens": 0, "agent_seconds": 0.0}
    for f in glob.glob("mcpmark/results-geode-agentworld/*/*/run-*/*/meta.json"):
        d = json.load(open(f))
        t["tasks"] += 1
        t["passed"] += 1 if d["execution_result"].get("success") else 0
        tu = d.get("token_usage") or {}
        t["input_tokens"] += tu.get("input_tokens") or 0
        t["output_tokens"] += tu.get("output_tokens") or 0
        t["agent_seconds"] += d.get("agent_execution_time") or 0
    print("mcpmark:", t)


def tau2() -> None:
    t = {"runs": 0, "episodes": 0, "reward_1": 0, "reward_below_1": 0, "no_reward": 0}
    for f in glob.glob("tau2/simulations/*/results.json"):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        t["runs"] += 1
        for s in d.get("simulations", []):
            t["episodes"] += 1
            r = (s.get("reward_info") or {}).get("reward")
            if r is None:
                t["no_reward"] += 1
            elif r >= 0.999:
                t["reward_1"] += 1
            else:
                t["reward_below_1"] += 1
    t["dirs_without_results"] = len(glob.glob("tau2/simulations/*")) - t["runs"]
    print("tau2:", t)


def crucible() -> None:
    verdicts = Counter()
    reasons = Counter()
    usage = Counter()
    for f in glob.glob("crucible/runs/campaigns/*/state/attempts/*/verdict.json"):
        d = json.load(open(f))
        verdicts[d.get("verdict")] += 1
        reasons.update(d.get("reasons") or [])
        for k, v in (d.get("usage") or {}).items():
            if isinstance(v, (int, float)):
                usage[k] += v
    print("crucible campaigns:", len(glob.glob("crucible/runs/campaigns/*")))
    print("crucible attempts:", len(glob.glob("crucible/runs/campaigns/*/state/attempts/*")))
    print("crucible verdicts:", dict(verdicts))
    print("crucible reject/invalid reasons:", dict(reasons))
    print("crucible verdict-attributed usage:", dict(usage))


def sil() -> None:
    evals = sorted(glob.glob("sil/petri-audits/*.eval"))
    span = (evals[0].split("/")[-1][:10], evals[-1].split("/")[-1][:10]) if evals else None
    print("sil petri audit logs:", len(evals), "date span:", span)


if __name__ == "__main__":
    mcpmark()
    tau2()
    crucible()
    sil()
