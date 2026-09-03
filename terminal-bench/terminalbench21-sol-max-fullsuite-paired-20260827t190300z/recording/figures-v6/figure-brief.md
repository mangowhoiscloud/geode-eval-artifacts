# Terminal-Bench 2.1 evidence figures — v6

These figures answer the evaluation question before explaining the procedure.
They are derived views, never score authority. Source authority remains Harbor
results and verifier receipts materialized through `native-results.json` and
`outcomes.json`.

| Figure | x | y | Encoding | Claim supported |
|---|---|---|---|---|
| Measurement cascade | measurement stage | selected cells | line, point and branch annotation | 890 intended cells become 870 executed, 864 valid and 675 passes; exclusions, invalid cells and semantic zeroes are distinct |
| Pass-rate comparison | verifier pass rate (%) | scope and harness | marker shape plus direct label | GEODE leads by 8 passes / 1.86 pp only on the exact 429 common cells; secondary denominators differ |
| Paired outcomes | paired outcome | exact-common cells | bars plus direct count | the observed edge is 53 GEODE-only minus 45 Codex-only cells, not an unpaired mean artifact |
| Task heterogeneity | task-level pass-rate delta (pp) | ranked runnable task | point sign and direct count | direction is symmetric across tasks (16 / 55 / 16) and the pooled edge is task-dependent |
| Task extremes | exact-common task pass-rate delta (pp) | task ID | lollipop and direct count | a few large, opposing task reversals create the small aggregate difference |
| Failure decomposition | count | failure class | horizontal bars and direct count | protocol-valid zeroes and infrastructure-invalid attempts are different populations and must not be pooled |

Statistical context uses 20,000 task-cluster bootstrap resamples with seed
`20260904`. The task, not the cell, is the resampling unit. The percentile
interval is descriptive uncertainty for this completed local diagnostic, not a
leaderboard confidence claim.

Design rules: opaque white canvas; black and gray structure; color only for
data state; marker shape and direct labels repeat every color distinction;
zero baselines where counts are plotted; no decorative cards or colored
borders.
