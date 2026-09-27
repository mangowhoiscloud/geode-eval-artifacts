# U4 / X2: full-matrix post-hoc numeric-parser correction

**This is a new offline post-hoc bug-correction analysis, not the original
preregistered result and not a new model experiment.** The user authorized
measurement of missing results. `contract.json` fixed the scope, source,
script, inputs and unchanged statistical rules before these corrected
outcomes were produced. Original runs and analyses remain immutable.

| Unit | Original Jev / Astra | Corrected Jev / Astra | Corrected difference | Original-rule 95% cluster interval | Registered-rule interpretation |
|---|---|---|---|---|---|
| U4 | 58/80 / 79/80 | **59/80 / 79/80** | **−25.00 pp** | **[−35.228944, −16.250000] pp** | `not-supported` remains; interval upper bound is below −10 pp |
| X2 | 194/240 / 226/240 | **196/240 / 226/240** | **−12.50 pp** | **[−17.216117, −8.044828] pp** | `mixed` remains; non-inferiority is unproven and the whole interval is below zero |

The numerical bug explains a small part of the observed gap, not the entire
gap. All five formerly rejected orders are accepted by the corrected numeric
parser, but only one U4 pool and two X2 pools gain a correct selected candidate.
The registered −10 pp margin itself still lacks an independently established
service-utility justification. Reusing it here describes the original rule;
it does not validate that rule's practical acceptability.

## What was recomputed

- **All 1,920 cells** were checked against the original frozen matrices:
  U4 80 pools × 3 selectors × 2 orders = 480; X2 240 × 3 × 2 = 1,440.
- **All 640 Jev pointwise responses**, not only the five rejected responses,
  were passed through both the original and corrected typed numeric parser.
  Every old admission decision was reproduced. The original sum tolerance
  0.025 and Score/distribution tolerance 0.03 were retained.
- **All 640 Astra pointwise responses** were decoded and checked against the
  unchanged numeric schema, recorded score vectors and code-owned winner.
- The **640 Astra listwise observations** retained their native winners and
  validity. Their raw provider response bodies are absent from dispatch
  records; no claim of raw-response reparsing is made for these cells.
- The unchanged native `_pointwise_outcome`, `_listwise_outcome`,
  `_acceptable_value` and `summarize_outcomes` owners re-created the original
  complete outcomes and summaries exactly before corrected outcomes were
  computed. The original CI was also reproduced exactly as a baseline gate.
- The existing `score_main_analysis.interval` bridge reused the native
  source-cluster percentile bootstrap: **2,000 resamples**, the original
  manifest/metric seed, **45 U4 clusters / 94 X2 clusters**, the same paired
  resampling and complete planned denominators. X2 split summaries and
  intervals were recomputed under their original seeds as well.

The current code revision is
`802cfd4b9d3220ce2be1744e8cf22161345b0954`. Its Score selection, candidate
projection and statistical owner files are byte-identical to the original
U4 source #2 and X2 source #5 files. The common numeric parser is the changed
owner. The correction compares validated JSON numbers' decimal representations
exactly at the existing boundary, without adding tolerance slack.

No prompt, model, provider, grade, candidate ID, presentation order, split,
cluster, seed, repetition, denominator or runtime budget was changed. Existing
provider-completion admissibility remains the original observation; the
analysis corrects stored numeric response admission and downstream selection.
No new oracle was run. Grades came from the previously approved native outcome
rows, whose IDs and byte digests are fixed in the contract.

## Exactly which selections changed

| Unit / pool ID | Original selection | Corrected selection | Grade / correct |
|---|---|---|---|
| U4 `q-f0cb080b1a85dd8d` | none, rejected order | `s-904f64018e74293d` | 3 / yes |
| U4 `cl-s14-bedding--q2` | none, rejected order | `cl-s14-bedding--q2b` | 0 / no |
| X2 `x2-8c78199b1ef8b24a` | none, rejected order | `c-da1c985fa130` | 0 / no |
| X2 `x2-711955ded266ee0e` | none, rejected order | `c-cdcea0e9da18` | 3 / yes |
| X2 `x2-d8e49616d1111f42` | none, rejected order | `c-b935bb93d2e6` | 3 / yes |

`U4-cell-audit.json` and `X2-cell-audit.json` cover every cell and bind raw
answer/question hashes. The additive `numeric-responses.jsonl` now supplies exactly the 1,280 audited pointwise parser-input strings, linked to those hashes. The corrected
results retain all pool outcomes and changed-pool before/after records.
`receipt.json` binds the contract and output files and records preservation
of **24 original files**, checked before and after, with **0 model calls** and
**0 original writes**. Original primary analyses were not appended, replaced
or reclassified.

## Reproduce the offline correction

Use a fresh output directory with the bound `contract.json` and `remeasure.py`,
the authorized original program directory and the named GEODE checkouts. Run
with the original installed environment; no network or authentication is used:

```sh
PYTHONDONTWRITEBYTECODE=1 python remeasure.py \
  --contract NEW_CORRECTION_DIRECTORY/contract.json \
  --program ORIGINAL_PROGRAM_DIRECTORY \
  --source GEODE_802CFD4_CHECKOUT \
  --original-source GEODE_1F6553431_CHECKOUT \
  --output NEW_CORRECTION_DIRECTORY
```

The script refuses to overwrite output files. The original parser SHA is the
same in both historical source pins. This original private recipe remains unchanged and still requires its authorized local records; it is not the public reader entry point.

## Public parser-to-result reconstruction

Use the [public reproduction recipe](../../REPRODUCE.md) with `--mode score-corrected`. The pinned native parser and selection owners reconstruct every corrected outcome from `numeric-responses.jsonl` plus the original public dispatch observations. They then recompute the summary, paired difference, decision under the original −0.10 rule, split statistics and the same cluster-bootstrap intervals, comparing the numerical objects exactly with the already published correction. The original native and corrected result files are unchanged.

The sidecar contains U4 160 Astra + 160 Jev and X2 480 Astra + 480 Jev pointwise answers. Each string retains its exact UTF-8 value and raw SHA, with unit/pool/selector/order, original dispatch SHA, one-based line, JSON pointer and question SHA. Astra strings contain only `c0`…`c3` numeric scores. Jev strings contain only typed scores, confidence, numeric probabilities and the unchanged public four-level rubric. The disclosure audit checks the complete 1,280-string scope and rejects other string fields; task/candidate bodies, private reasoning, provider payloads, authentication, account identity and personal paths are absent. Jev answers are the adapter’s serialization of the answers object, not the original HTTP wire body.

All 1,920 cells remain in the reconstruction. The 640 Astra listwise cells use their retained native winner observations because their raw responses are unavailable. This is a precise remaining reproduction boundary, not a claim to have replayed those raw responses. Mind2Web task/candidate text remains excluded.

[`numeric-response-disclosure.json`](numeric-response-disclosure.json) binds the sidecar, its scope checks and this README revision. `publication-map.json` keeps all original source SHA values and the seven unchanged scientific-artifact entries. Its README entry now records the current public digest, the previous public digest and the reason for the documentation revision; it is explicitly not byte-identical to the original source README. Its `raw_response_bodies_included: false` describes the original eight-file projection; the separate numeric sidecar is bound by the additive disclosure receipt. The original contract, result, cell-audit, remeasurement script and receipt bytes remain unchanged.
