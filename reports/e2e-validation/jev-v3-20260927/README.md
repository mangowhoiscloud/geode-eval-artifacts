# Jev v3 main study: results, verifier defects and reproduction

This packet explains the 2026-09-27 Jev/Astra study and preserves its result and failure lineages. It asks which bounded judgments can be delegated, whether probabilities help identify errors, and whether those decisions lead to actual task completion. **It does not reduce all measurements to one model ranking or one combined success rate.**

**Staging status:** the pre-E8, 8,655-file packet completed its model-free validation and supported result-recomputation path successfully. E8 evidence has now been added as a separate lineage; final checks for those additions and publication integration are still in progress. U4/X2 have a measured post-hoc numeric-parser correction, and interrupted E8 U8n has a separately labeled complete-pair descriptive analysis. The packet is not yet remotely published. See [reproduction scope](REPRODUCE.md) and [scoring rules](SCORING.md); neither disclosure nor a successful calculation reconstructs every private input or the original live environment.

## Start with the answer

- [한국어 상세 해석](INTERPRETATION.ko.md): 기능별 결론, 확률과 오류 선별의 차이, E2E의 천장 효과, verifier 결함의 원인·대응·수정 전후 결과.
- [English findings](INTERPRETATION.md): concise results and the decisions they support.
- [Measured U4/X2 post-hoc correction](corrections/numeric-parser-20260928/README.md): complete matrix, changed selections, unchanged statistical rules and preserved original results.
- [E8 U8n observed-pair analysis](analyses/u8n-observed-pairs-20260928/README.md): the post-hoc 11-pair sample, candidate correctness versus delivered success, and its public reproduction inputs.
- [Earlier M4–M6 pilot](../jev-verdict-20260924/README.md): a separate historical diagnostic, not part of the main-study denominators.

The bounded intent/target panel supported further investigation of delegation. Noul joint judgments and Score candidate selection showed substantial losses. After actual full-matrix numeric-parser correction, U4 is Jev **59/80 vs Astra 79/80, Δ −25.00 pp, 95% CI [−35.23, −16.25]**; X2 is **196/240 vs 226/240, Δ −12.50 pp, CI [−17.22, −8.04]**. The original-rule decisions remain `not-supported` for U4 and `mixed`/unproven non-inferiority for X2. These are post-hoc corrected results, not new model samples. Choice remained uncertain against its registered loss margin. Jev's judgment responses were faster, but the natural-task experiment did not exercise judge fallback and could not establish its practical utility.

E8 U8n adds a concrete failure mechanism: **in 11 complete valid pairs, Astra-judged runs delivered 11/11 strict recoveries and Jev-Noul-judged runs delivered 0/11, although the latter's last candidates passed the existing task oracle in all 11 cases.** Both arms used Astra for root execution and repair. Jev continued to label the repaired, supported candidates as lacking evidence, so delivery was held. This is a post-hoc observation from four source tasks after an infrastructure stop, not a confidence interval, non-inferiority result or general reliability estimate. The original 36-cell/18-pair plan and null primary result remain intact.

## Follow a result to its evidence

Start from the public unit index, select the study unit and execution lineage, then read its frozen specification, selected attempts, native result and analysis. Use the analysis pointer to check the exact numerator, denominator and source result. Inspect the verifier or defect audit when the outcome depends on a contract or measurement failure. Match file digests before comparing versions.

Use [units.json](units.json) for the 27 registered units and original/current lineage pointers. For panel data, read [PANEL-DATA.md](PANEL-DATA.md) and the [source-to-public map](evidence/panel-source-map.json); for the newer U4/X2 result, read the [correction receipt](corrections/numeric-parser-20260928/receipt.json). The unit index preserves the registered-study results; the separate correction package owns the post-hoc U4/X2 results shown above. [E2E-DATA.md](E2E-DATA.md) distinguishes the original 15 lineages from the additive [E8 source map](evidence/e2e-source-map-e8.json) and its 760 disclosed files. The separate observed-pair analysis owns the E8 candidate-level diagnosis; it does not replace native rewards or the original primary result. The [I5](study/audits/i5-natural-audit/audit.json), [I6](study/audits/i6-natural-audit/audit.json), [E6](study/audits/e6-u7r0-diagnosis/diagnosis.json) and [numeric-validator](study/audits/numeric-tolerance-fix/closure.json) audits explain the relevant failure and repair lineages.

The native result and verifier receipt own the recorded outcome. The analysis explains the registered metric. These interpretation documents explain its scope; they do not replace either authority. A terminated process, accepted helper output, recorded candidate, complete trajectory or integrity check is not itself strict task success.

## Choose the activity you intend

| Activity | Required material | Calls and limitations |
|---|---|---|
| Read and verify integrity | Pinned code revision, unit index, manifest and file digests | Local checking makes no model calls. Matching hashes establish byte identity, not correctness of the score. |
| Recompute retained results | Public predictions, permitted gold or labels, grouping/cluster metadata, frozen selection rules and the pinned native analyzer | Can be offline after required inputs are available. A correctness tally is not the complete analysis. Missing inputs must be reported per unit; full-study recomputability is not assumed. |
| Run a new experiment | Provider credentials, an authorized account and budget, environment, task inputs and a new frozen run specification | Makes new hosted calls and may incur charges. It is a new nondeterministic run and need not reproduce the original numbers. Reading this packet does not launch it. |
| Inspect a trajectory or replay | Disclosed events or a selected replay, source clock/speed and omission metadata | Viewing makes no model calls. A digest cannot reconstruct withheld text. A replay is behavior evidence, not the score or latency authority. |

For X2, follow the official source, pinned conversion procedure and hashes. Do not infer that this packet redistributes the original test text or candidate pools. Disclosure and input availability must be checked in the finalized index before claiming an independent recomputation.

## Review with an agent

Give the agent one result and request a read-only trace from unit ID to pinned source, specification, attempts, native counts and analysis. Ask it to report disagreements, missing inputs and the exact scope it could verify. Keep experiment APIs, credential changes, paid calls, rescoring and T/τ refitting outside that review. A missing input is a reported boundary, not permission to silently replace it with a new run.

## Keep failure lineages separate

I5's task-contract omission and ambiguous evidence timing affected the final judge; I6 is the separate corrected execution. U4/X2's floating-point boundary rejection is a different measurement defect: the measured full-matrix correction improves Jev selection by one U4 pool and two X2 pools, while substantial accuracy gaps remain. E6 infrastructure-invalid and unstarted cells and E7 completed runs remain separate. The earlier U8n lineage retains its 36 unexecuted runs after a failed prerequisite. Source7/E8 later passed U0e admission 2/2, then stopped U8n after 24 of 36 planned cells: 23 valid, one injection-evidence invalid and 12 unstarted. Its registered primary remains not-measurable with null numerator and denominator. At the user's direction, no further U8n live run is planned; the separate descriptive analysis uses the 11 pairs whose two arms both finished validly, excluding the invalid B cell and its successful A partner symmetrically. The interpretation documents preserve old failures and distinguish subsequent observations without pooling them.

The registered −10 pp non-inferiority margin is not presented as a business-derived acceptable loss. The study does not establish general production reliability, causal benefit from recovery lineages, or end-to-end invoice savings.
