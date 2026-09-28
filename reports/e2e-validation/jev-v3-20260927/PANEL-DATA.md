# Jev v3 panel evidence: original runs and public projections

This is a retrospective publication of the original panel/Score experiment
records, including preparations, blocked starts and incomplete predecessors.
It makes no new model calls and does not replace the frozen native analyses.
The public files are **projections**, not byte-identical native run bundles.
Repository publication and remote read-back are separate from this export.
The packet was merged into `main` by
[PR #46](https://github.com/mangowhoiscloud/geode-eval-artifacts/pull/46)
(merge commit `3bcf4044`) and is publicly readable on GitHub.

Start with [the source/public map](evidence/panel-source-map.json), then the
run-specific `analysis.json` and its `results.json` references. The map lists
every regular file inventoried across `jev-panel` and `jev-panel-r1` through
`jev-panel-r7`, with source SHA-256, public SHA-256, sizes and changed JSON
pointers or a whole-file exclusion classification. Paths are relative to the
operator-supplied program directory; private machine roots are not published.
The map covers 3,505 files: 3,146 public JSON/JSONL projections, 240 excluded
implementation/cache/log files and 119 withheld generation event/response
files. The original `jev-panel-r4/u0b-pool` directory symlink is not followed;
the source generation records are retained under `jev-panel-r3/u0b-pool`.

## Read a result and its observations

| Measurement | Current original result | Row-level observations |
|---|---|---|
| Selection, calibration and thresholds | [r5 U1 freeze](evidence/panel/jev-panel-r5/u1/selection-freeze.json) | U1 choice/noul `receipts/`, attempts and analyses; prior r4 interruption is separate |
| Held-out Choice / Noul | [Choice](evidence/panel/jev-panel-r5/u2/choice/results.json), [Noul](evidence/panel/jev-panel-r5/u2/noul/results.json) | Each engine receipt preserves state/cluster IDs, prediction, probabilities, validity, latency and usage |
| Repetition and paraphrase stability | [Choice](evidence/panel/jev-panel-r5/u2s/choice/stability-results.json), [Noul](evidence/panel/jev-panel-r5/u2s/noul/stability-results.json) | `runs`, `variants` and original receipts preserve the separate repeated/modified inputs |
| Isolated judgment latency | [r5 U3](evidence/panel/jev-panel-r5/u3/choice/latency-results.json) | `pairs`: native times, paired differences, cluster IDs and exclusion reasons |
| Controlled candidate selection | [r5 U4](evidence/panel/jev-panel-r5/u4/results.json) | `outcomes`: grades, candidate IDs, mean scores, selected IDs, per-order validity and oracle outcomes; `dispatch-records.jsonl` retains parsed response fields |
| Natural generation and selection | [r5 U5p](evidence/panel/jev-panel-r5/u5p-pool/results.json), [r5 U5s](evidence/panel/jev-panel-r5/u5s/results.json) | Authored task and visible candidate JSON in `pools.natural.jsonl`; generation usage and per-pool Score outcomes |
| Intent and target | [r4 U6a](evidence/panel/jev-panel-r4/u6a/choice/intent-results.json) | `items`: 220 gold/prediction/correctness rows in 40 families; helper probabilities in receipts |
| External completion judgments | [r5 X1](evidence/panel/jev-panel-r5/x1/choice/x1-results.json) | Parsed predictions/probabilities and cluster IDs in 478 receipts; result contains aggregate reference-label comparisons |
| External candidate selection | [r7 X2](evidence/panel/jev-panel-r7/x2/results.json) | 240 outcome rows with grades/IDs/scores/order choices; 1,440 selector-order records in dispatch data; no Mind2Web task/candidate text |

The denominators and confidence intervals remain those of the original
analyses. Selection calibration is not held-out validation. U4 combines the
registered selection and test pools. Candidate width, presentation order,
repeated requests and source clusters are not interchangeable sample counts.
No counts from different studies are pooled into one success rate.

Earlier account/initialization/budget/transport failures remain under their
original run-directory names. An incomplete predecessor is not a fresh
semantic failure and a successful later lineage does not erase it. The
recorded U4 two / X2 three numerical-parser boundary rejections remain in
these original scores. The [completed corrected analysis](corrections/numeric-parser-20260928/README.md)
is a separately named post-hoc result and does not overwrite this evidence.

## Public boundary

- Numeric predictions, distributions, selected IDs, grades, correctness,
  clusters, timing, source versions, denominators, CI parameters and missing
  usage (`null`) are retained. Subscription token counts are not invoices.
- Raw response strings, response tracking IDs and model response/feedback
  explanations are removed from individual receipts and Score dispatches.
  Parsed typed answers are retained. Hidden reasoning is not published or
  reconstructed; reasoning **token counts** and configured effort are distinct.
  A separately reviewed [numeric-response sidecar](corrections/numeric-parser-20260928/numeric-response-disclosure.json)
  preserves 1,280 numeric-only U4/X2 parser inputs for independent reanalysis.
  It contains no task/candidate bodies or reasoning. Jev entries are the
  adapter's retained answer serialization, not complete HTTP response bytes;
  Astra listwise winners remain observed records without response re-parsing.
- Native generation event streams and child-agent response bodies are
  withheld as whole files. The visible final synthetic candidates and
  generation usage remain available in their native pool/usage views.
- Authored synthetic inbox/answer inputs in the normalized U0b pools and
  natural candidate pools are included. X1 external task/trajectory text,
  Mind2Web task/candidate text, upstream archives and unopened sealed packs
  are not included. External reconstruction requires the separately pinned
  upstream data and transformation contract, subject to its terms.
- Account fingerprints, authentication fields, email patterns and private
  machine paths are removed or masked. Path-valued hash-map keys receive a
  digest suffix to avoid collapsing distinct native inputs.

Native `schema_id` and digest fields are preserved to identify the producing
contract and source bytes. **A source digest inside a projected file must not
be used as the digest of its public counterpart.** Resolve the relative
source path through `panel-source-map.json` to obtain the public digest.
The native `validate-run-bundle` contract is not claimed to pass on redacted
copies; its immutable original success remains separate evidence.

## Verify and reaggregate offline

From this directory, Python 3.12+ is sufficient for the publication check:

```sh
python tools/export_panel.py --output . --verify-only
```

The [verification receipt](evidence/panel/verification.json) checks every
public file hash and 328 native metric JSON pointers. It also reaggregates
U4 −21/80, U5s 0/12, X2 −32/240, U6a −4/220 and U3's paired median difference
of −10.201182917 seconds from public observation rows. During export, the
scientific result/CI/decision fields are compared directly with their native
source objects, and all source file hashes are checked for preservation.

This check does not rerun a bootstrap or reinterpret a model response.
Per-row outcomes, cluster IDs, the original method, 2,000 replicates and seeds
are available for U3/U4/U5s/U6a/X2 interval reconstruction using the pinned
GEODE analysis owner. For U1/U2 and X1, reproducing the original score/CI from
predictions additionally requires the authorized label, alias and split
manifest projections in the complete publication package; receipts alone do
not supply missing labels. The complete package includes [approved test labels](study/inputs/test/gold.test.jsonl),
[aliases](study/inputs/test/aliases.test.json), [public test split](study/inputs/test-public/split-manifest.json)
and [selection labels](study/inputs/selection/gold.selection.jsonl).
This panel component does not read an unopened sealed directory to fill that dependency.

To reproduce publication from an authorized local program directory, use a
new destination (the exporter refuses to replace an existing source map):

```sh
python tools/export_panel.py --input PROGRAM_DIRECTORY --output NEW_PACKAGE
```

No network, authentication access, live execution, data tuning or new statistical
model is used by the exporter. Unreviewed research file names fail closed;
symlinks are listed without following their targets.
