# How the study scores a result

A model response, an internal verifier decision and a final task score answer different questions. This packet keeps their producers and denominators separate.

| Stage | Producer and retained evidence | Reader and decision |
|---|---|---|
| Response admission | Typed validator → receipt acceptance, scores/labels and failure class | Panel analyzer admits a structured response. Well-formed output alone is not a correct answer. |
| Component accuracy | Frozen synthetic gold or external labels → item-level correctness | The analyzer compares each engine against the same labels and groups related items by source cluster. |
| Root continuation | Internal LLM/Jev verifier → supported/contradicted/missing-evidence decision and feedback | The root either delivers, repairs within the original deadline, or withholds delivery. |
| Task outcome | Separate task-owned verifier → verifier receipt and strict/recovery result | The E2E analyzer scores the completed task. Internal acceptance cannot substitute for this outcome. |
| Study conclusion | Frozen analysis rule → paired difference and cluster interval | The registered margin determines supported/not-supported/mixed for that specific claim, not a universal model ranking. |

## Candidate selection: one pool, two orders, one primary observation

U4 and X2 compare pointwise candidate selection. Both engines score the same four candidates in forward and reverse order. The analyzer aligns candidate IDs, averages each candidate's two scores, then selects the maximum using the frozen tie rule. Selecting any candidate with the highest fixed grade earns one point for that pool. For example, grades `[3,2,0,0]` and an average-score winner at candidate 2 produce 0/1, even when both responses were well formed. Two orders are not two independent pools.

A model output validation error or fallback in either order contributes zero for that pointwise pool under the registered rule; it remains in the planned denominator. Infrastructure-invalid execution and an unstarted unit instead retain unknown/not-measurable status. The sidecar validity and the metric's zero policy are distinct fields.

The supplementary Astra listwise selector averages the correctness of its two observed winners, so its pool contribution can be 0, 0.5 or 1. It does not use the pointwise averaging rule.

[Corrected U4/X2 evidence](corrections/numeric-parser-20260928/README.md) reparses the retained numeric responses with the repaired decimal boundary comparison. Gold, candidate order, cluster membership, tolerances and planned denominators are unchanged. This is an offline post-hoc software correction, not a fresh model sample.

## Component and E2E denominators

- U2 Choice compares the verdict with fixed gold. Noul joint correctness requires both conditions to match; satisfying only one is insufficient. The primary in-scope population is 216 states; the 24 outside-scope states are reported separately.
- U6a joint intent/target correctness requires both outputs to match for each item; the 220 items belong to 40 families. Its 95% interval is a 2,000-replicate family/source-cluster percentile bootstrap, not a simultaneous interval.
- U4 counts 80 pools: 32 selection and 48 test. X2 counts 240 transformed four-candidate steps, not whole web tasks.
- U7 uses 12 independent tasks, three arms and two recorded repetitions. Its 72 trials do not make 72 independent tasks. The recorded cascade fallback count is zero; this does not measure fallback benefit.
- E2E primary differences are computed only for a complete eligible unit. Natural tasks use strict success, injected tasks use recovery. A preserved failure or an invalidated run is not silently replaced by a later success.

Confidence intervals resample the registered source units (families, source clusters or websites), not individual calls. The `confidence_interval` or `interval` field records the seed, replicate count, grouping and method. Calibration, error ranking, latency and end-to-end success are separate measurements.

## U8n: a correct repaired candidate and successful delivery are separate

The [E8 post-hoc analysis](analyses/u8n-observed-pairs-20260928/README.md) includes every observed pair whose two arms completed validly: 11 pairs from four source tasks. It does not replace the original 36-trial primary, which remains invalidated with null counts after 24 observed trials (23 valid, one invalid) and 12 unstarted trials. The condition denominators are four contradiction-only, four missing-evidence-only and three combined-fault pairs; no interval or non-inferiority conclusion is added.

Both arms use Astra for execution and repair. The final candidate state contains the task contract, original request, visible candidate and actual tool observations. Recomputing this state with the existing rule-based scorer finds correct, evidence-supported candidates in all 11 trials per arm. The Astra judge permits final delivery in 11/11; the Jev judge continues to report missing evidence and withholds delivery in 11/11. The native recovery metric requires the first negative judgment, consumption of that feedback and final task reward. A correct intermediate candidate alone cannot satisfy that metric. Native strict/recovered values therefore remain A 11/11 and B 0/11. The separate candidate diagnosis explains the observed delivery failure without rewriting native outcomes.

## Source owners

The [public unit index](units.json) links the frozen specification, attempts and analysis to the original source revision. For the corrected candidate analysis, the pinned owners are [score selection](https://github.com/mangowhoiscloud/geode/blob/802cfd4b9d3220ce2be1744e8cf22161345b0954/evals/benchmarks/score_selection.py), [cluster metrics](https://github.com/mangowhoiscloud/geode/blob/802cfd4b9d3220ce2be1744e8cf22161345b0954/evals/benchmarks/decision_metrics.py) and [typed response validation](https://github.com/mangowhoiscloud/geode/blob/802cfd4b9d3220ce2be1744e8cf22161345b0954/core/llm/adapters/typesafe.py). The [handoff runtime and semantic oracle](https://github.com/mangowhoiscloud/geode/blob/1236ce96c8c5a79699d98f5c960b7a699c1f228a/evals/benchmarks/decision_handoff_runtime.py) keep internal judgments and task-owned outcomes separate.
