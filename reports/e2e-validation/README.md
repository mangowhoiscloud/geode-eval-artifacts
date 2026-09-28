# Research and E2E validation records

This index separates study protocols, runtime checks and subsequent analyses.
Dates below describe the study or analysis; a later repository merge does not
turn a historical run into a new observation.

## Jev / Astra: choose the question

| Question | Read | Scope |
|---|---|---|
| What does the study conclude? | [Jev v3 overview](jev-v3-20260927/README.md) · [한국어 해석](jev-v3-20260927/INTERPRETATION.ko.md) · [English findings](jev-v3-20260927/INTERPRETATION.md) | September 27–28 main-study results, with distinct functional metrics and execution lineages |
| How are predictions and completed tasks scored? | [SCORING.md](jev-v3-20260927/SCORING.md) | Candidate selection/grades, internal completion judgments and independent task verification have different authorities |
| What are the units, settings and source data? | [27-unit index](jev-v3-20260927/units.json) · [source inventory](jev-v3-20260927/SOURCES-AND-DISCLOSURE.md) · [panel data](jev-v3-20260927/PANEL-DATA.md) · [E2E data](jev-v3-20260927/E2E-DATA.md) | Follow the selected unit's specification, split, model route, attempt/result and analysis; units are not interchangeable denominators |
| Which U4/X2 numbers include the measured parser correction? | [Numeric-parser correction](jev-v3-20260927/corrections/numeric-parser-20260928/README.md) | Full retained matrices re-evaluated under the recorded correction; original results preserved, no new model samples or threshold refitting |
| Why did correct U8n candidates remain undelivered? | [Observed-pair analysis](jev-v3-20260927/analyses/u8n-observed-pairs-20260928/README.md) | All 11 complete valid pairs, four source tasks, after the infrastructure stop; descriptive post-hoc analysis, not completion of the original 36-cell plan |
| Can a reader reproduce a reported number? | [REPRODUCE.md](jev-v3-20260927/REPRODUCE.md) and the separate correction/observed-pair guides above | Supported public-input calculations make no model calls. A new live experiment is a separate, nondeterministic activity |
| What preceded the main study? | [September 24 final-verdict pilot](jev-verdict-20260924/README.md) · [normalization](jev-verdict-20260924/NORMALIZATION.md) | M4 natural rollouts, M5 same-snapshot judgments and M6 controlled recovery; not pooled into v3 |

For a first reading, use the v3 overview → scoring → interpretation → unit and
source records → reproduction guide. Read the earlier pilot when comparing
study designs; its authored tasks, repetitions and interventions have their
own denominators. Astra executes and repairs across the E2E conditions.
Changing the judgment policy is not a comparison of complete agent products.

### Frozen evidence and current guidance

The original v3 packet was published by [PR #46](https://github.com/mangowhoiscloud/geode-eval-artifacts/pull/46)
at [`3bcf4044eb5c2411dd48122d672aef72a83fb30e`](https://github.com/mangowhoiscloud/geode-eval-artifacts/tree/3bcf4044eb5c2411dd48122d672aef72a83fb30e/reports/e2e-validation/jev-v3-20260927).
Check its frozen `publication-manifest.json` against that revision. Current
Markdown can clarify publication status without rewriting that historical
commit. Original native results, post-hoc corrections and observed-pair
analyses keep separate authority; an unavailable primary result is not zero.

The [trajectory contract](../../TRAJECTORIES.md) applies to normalized
trajectory releases. A study packet has its own manifest and disclosure
limits; its presence here does not imply full byte replay or availability of
private prompts, provider reasoning or credentials.

## Earlier feature and benchmark validation

The date-prefixed files in this directory preserve their original conditions.
Useful entry points include the [July 31 GPT-5.6 benchmark](2026-07-31-gpt56-benchmark.md),
[August 3 Tau2 full cycle](2026-08-03-gpt54-tau2-full-cycle.md),
[August 4 infrastructure diagnostic](2026-08-04-gpt54-runtime-faithful-tau2-diagnostic.md)
and [August 12 matched token diagnostic](2026-08-12-mcpmark-geode-gpt54-token-efficiency-rerun.md).
The [repository README](../../README.md#current-focused-datasets) also indexes
Terminal-Bench, skill-attribution and other datasets stored outside this directory.
