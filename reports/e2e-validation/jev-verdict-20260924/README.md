# GEODE final-verdict comparison: LLM and Jev

Reviewed public projections of three small, authored diagnostics. The root
agent and cognitive calls use **GPT-6 Astra, subscription route, xhigh**. Only
the typed final-verdict provider changes: Astra in arm A, direct TypeSafe
**Jev 1.13** in arm B. Rejected judgments use code-owned repair feedback.
The studies do not compare two complete agent products or model families.

This directory is a **retrospective publication projection**, not a new
experiment, official benchmark, training dataset, or promotion decision.
The original prospective contracts and their digests remain separately
identified. Preparation creates no model calls. The publication manifest's
status records local preparation; repository merge and remote read-back are
separate operations.

## Read the evidence

| Study | Unit and result | Start here | What it can establish |
|---|---|---|---|
| M4: natural rollouts | Three authored inboxes × two repetitions × two engines; A 6/6 and B 6/6 successful | [Results](natural/results.json), [analysis](natural/analysis.json), [original contract](natural/source-contract.json) | Observed time, calls and usage under independent rollouts with the same semantic contract. All judgments accepted; this cohort provides no repair evidence. |
| M5: same-snapshot judgments | Three observed states of one authored task × two engines; both matched all three expected labels | [Results](snapshots/results.json), [analysis](snapshots/analysis.json), [original contract](snapshots/source-contract.json) | Typed judgments on identical state input. Projected repair branches were not consumed by a root agent. |
| M6: controlled recovery | One order-status task × two candidate interventions × two engines; both closed both repairs | [Results](recovery/results.json), [analysis](recovery/analysis.json), [original contract](recovery/source-contract.json) | Rejection → root consumption → evidence/candidate repair → re-verification → independent oracle. Injected bad candidates are controlled interventions, not naturally occurring model errors. |

The paired primary difference is 0/6 for M4 and 0/2 for M6. Repeated runs are
not independent task families. M5's six calls are not rollouts, and none of
these denominators includes admission or invalid attempts. The Jev premature
candidate was labeled `contradicted` rather than the expected
`insufficient_evidence`; both labels rejected delivery, and the resulting
repair still completed. This distinction is retained rather than hidden by
the final success count.

### Preserved lineage

- [Natural admission](admission/natural/results.json): two valid checks.
- [Recovery admission](admission/recovery/results.json): two valid checks,
  explicitly reused after infrastructure recovery; not new observations.
- [Collector-invalid predecessor](invalid/collector/results.json): one
  observed attempt, one unexecuted cell. A native pass did not make the
  measurement valid.
- [Original recovery](invalid/recovery-original/results.json) and
  [second recovery](invalid/recovery-r2/results.json): each stopped after one
  infrastructure-invalid attempt; three cells remained unexecuted in each.
  Neither is scored as a task failure. The later four-cell run replaces their
  measurement role without deleting their original evidence.
- [Lineage](lineage.json) gives replacement edges and denominator boundaries.
  Aggregate attempt rows are bookkeeping, not additional calls or trials.

## Accounting and interpretation

Per-call and aggregate records retain input/output/cache/reasoning coverage,
known sums, missing-event counts, model purpose and latency. A missing cache
field is not zero; a known observed zero remains zero. Subscription
API-equivalent estimates, Jev input-tariff estimates, provider-reported cost
and actual charges remain separate. **Actual invoice charge is unknown** in
these records. No dollar amount here proves a subscription debit or invoice.

M4's approximately 17× judgment-response ratio and 7.5% lower whole-runtime
median compare arm medians across six observations per arm. They are not a
median of paired speedups or an estimated causal effect. M6 has a different
intervention protocol and cannot be subtracted from M4 as measured recovery
overhead. Inspect all paired observations, not only those showing a speedup.
The cognitive policy was shared, but realized cognitive calls differed
(A: 9, B: 12); root and verdict inputs were rollout-specific. Only M5 held
the observed state bytes identical across the two judgment engines.
The [12-call timing projection](natural/judgment-timing.json) exposes each
native duration, source SHA-256 and JSON pointer. Its arm medians are
7.235042420 s / 0.425829146 s for final-verdict responses (16.99048×), and
50.198481043 s / 46.439073209 s for runtime (7.48909% lower median).

## Files and normalization

```text
jev-verdict-20260924/
├── README.md, NORMALIZATION.md, normalize.py
├── publication-manifest.json, normalization-receipt.json, lineage.json
├── natural/                 # 12 independent rollouts
├── snapshots/               # 6 same-state component calls
├── recovery/                # 4 controlled-recovery rollouts
├── admission/{natural,recovery}/
└── invalid/{collector,recovery-original,recovery-r2}/
```

Each cohort contains the public `run-spec.json`, `attempts.jsonl`,
`analysis.json`, `results.json`, original `source-contract.json` view and
linked receipt projections. [NORMALIZATION.md](NORMALIZATION.md) describes
producer → field → public reader, removed content, exact digest joins, and
validation. Two independent `geode.trajectory@1` releases contain 12 natural
and four recovery trajectories; their paths and manifest hashes are listed in
[the normalization receipt](normalization-receipt.json). They are
scope-complete but **not byte-replay-complete**: private content is represented
by digests. There is no learning-view or training-readiness assertion.

Private prompts, candidate/tool bodies, provider reasoning, SQLite,
terminal recordings and authentication files are not public payloads. Native
verifier and source hashes remain the score and identity authorities; the
public views do not replace them.
