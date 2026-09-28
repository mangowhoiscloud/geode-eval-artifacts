# Jev v3: what the study supports

**Bounded intent-and-target classification was a plausible delegation candidate. Noul joint judgments and Score-based candidate selection performed substantially worse in the tested configurations.** Choice completion judgments had a small mean difference but too much uncertainty to establish the registered non-inferiority criterion. Jev returned individual judgments faster. The natural-task experiment, however, saturated at success for every arm and never invoked the conditional judge fallback, so it did not measure the practical benefit of escalation.

This report interprets the retained 2026-09-27 study, the **2026-09-28 full-matrix post-hoc numeric-parser correction of U4/X2**, and the interrupted E8 U8n complete-pair descriptive analysis. The U4/X2 headline rows use the measured corrected results; the original preregistered results remain separate and immutable. Neither post-hoc analysis made new model calls. The U4/X2 correction kept its margins, grades, denominators, order, clusters and resampling rules; the E8 descriptive sample is explicitly separate from its original plan and null primary. A is GPT-6 Astra with `xhigh`; B is Jev 1.13.0. Astra/GEODE still performed root execution and repair in the E2E experiments. The earlier [M4–M6 pilot](../jev-verdict-20260924/README.md) is separate. See the [detailed Korean interpretation](INTERPRETATION.ko.md) and [packet guide](README.md).

## Findings and decisions

Differences below are Jev minus Astra, in percentage points. U4/X2 intervals are from the post-hoc correction; other intervals are the retained main-study analyses. E8 U8n is a post-hoc partial sample and has no reported confidence interval or non-inferiority decision. States, items, candidate pools, tasks and calls are not pooled into one success rate.

| Measurement | Observation | What follows |
|---|---|---|
| U6a intent/target joint | 216/220 vs 220/220; Δ −1.82 pp, family-cluster bootstrap 95% CI [−3.65, −0.45] | Meets the registered −5 pp margin on 40 designer-authored families. It supports investigating this bounded classifier, with a small observed loss; it does not establish equivalence or generalization. |
| U2 Choice | 155/216 vs 157/216; Δ −0.93 pp, 95% CI [−9.72, +7.41] | The mean is close, but the interval includes losses beyond −5 pp. Blanket replacement on an assumption of negligible quality loss is unsupported. |
| U2 Noul joint | 55/216 vs 145/216; Δ −41.67 pp, 95% CI [−48.15, −35.19] | Large joint-accuracy loss argues against standalone replacement in this configuration. |
| U4 controlled selection — post-hoc corrected | 59/80 vs 79/80; Δ −25.00 pp, 95% CI [−35.23, −16.25] | Large top-1 loss; the denominator includes 32 selection and 48 test pools, not 80 held-out pools. |
| X2 external K4 selection — post-hoc corrected | 196/240 vs 226/240; Δ −12.50 pp, 95% CI [−17.22, −8.04] | Loss persists on transformed Mind2Web steps. The interval is below zero and crosses −10 pp; `mixed` does not mean no difference. This is not full web-task success. |
| X1 external completion judgment | 136/239 vs 125/239; Δ +4.60 pp, 95% CI [+0.41, +9.36] | A relative advantage on this text conversion, but Jev rejected 97 of 119 human successes; Astra rejected 113. Neither relative advantage nor a valid output establishes high absolute completion-judgment reliability. |
| E8 U8n — post-hoc complete valid pairs | Astra-judged strict/recovered 11/11; Jev-judged 0/11. Last-candidate task-oracle success 11/11 in both arms. | In these four source tasks, Astra repaired the candidates in both arms, but Jev Noul falsely rejected the supported candidates and held delivery. This diagnoses the observed hold; it is not a population effect or a replacement for the null registered primary. |

X1 omitted screenshots and actual tool-result content. Its result is conditional on that information loss. The retained-response audit also found that Jev predicted `missing_evidence=true` for all 216 primary Noul states, whose labels for that condition were balanced 108/108. This reveals an over-rejection pattern; it does not isolate provider implementation, model capability or question design as its cause.

The registered −10 pp selection margin is a comparison rule. The reviewed registration/audit material did not establish a derivation from business error costs or a service objective. It must not be presented as an operationally acceptable quality loss. The original margins and decisions remain unchanged.

**U6a interval-label correction:** the earlier film and initial explanation incorrectly called this a simultaneous interval. The native method is a source-cluster percentile bootstrap over 40 families with 2,000 resamples. This report corrects the method label without changing counts, interval values or the registered decision.

## Calibration, error ranking and repeatability

Jev had lower raw ECE (0.075 vs 0.260), but weaker error-detection AUROC (0.785 vs 0.879) and worse AURC (0.106 vs 0.073; lower is better). Thus better frequency calibration did not mean better separation of correct and incorrect decisions in this sample. The valid-probability denominators are Jev 215 and Astra 216.

Likewise, Jev Noul repeated the same response on 23/24 diagnostic states, yet both responses were correct on only 6/24. Consistency can preserve an error. `q=max(P)`, a separate native `confidence` field, and task success are distinct. Selection-fitted temperature is post-hoc probability calibration, not generation temperature; error ranking and cascade used raw q.

## Why successful execution did not establish fallback utility

E7 U7 ran the same 12 natural tasks in three arms twice: 72/72 strict successes, 24/24 per arm. This shows that the tested execution-and-delivery paths worked on that set. It is not evidence from 72 independent tasks. C accepted the Jev decisions in all 24 runs and made zero Astra judge fallbacks. Root/repair calls do not count as judge fallback. Consequently, the experiment did not observe the quality, latency or cost of actual escalation.

The offline frozen cascade was a different measurement: 160/216 vs Astra 157/216, Jev coverage 190/216, τ=0.5, with a difference interval [−6.48, +9.26] pp. It does not supply missing live fallback observations. U5 also saturated: first/random/oracle and the tested selectors all reached 12/12; `oracle coverage − random = 0`, so `gap_closed` was not measurable. That candidate set could not discriminate selector quality.

U8c did provide a positive bounded recovery observation: both arms repaired the three prescribed fault combinations across six source tasks, with all 36 runs succeeding after one replan. It is evidence about those faults and paths, not a general recovery guarantee.

### E8 U8n: repaired candidates were still denied delivery

The [observed-pair analysis](analyses/u8n-observed-pairs-20260928/README.md) separates candidate correction from actual completion. In both arms, GPT-6 Astra `xhigh` performed root execution and repair; the final judge was Astra for A and Jev Noul for B. After the injected fault, the next judged candidate was rule-supported in every included run. A then delivered all 11 answers. B's last candidates also passed the existing task oracle 11/11 and had rule gold `(c,m)=(0,0)`, yet Jev projected `(0,1)`—no contradiction, but missing evidence—and all 11 deliveries were held with `external_verification_required`.

| Injected condition | Complete valid pairs | A strict / recovered | B strict / recovered | B last-candidate oracle pass / false rejection |
|---|---:|---:|---:|---:|
| c1m0: contradiction only | 4 | 4/4 | 0/4 | 4/4 / 4/4 |
| c0m1: missing evidence only | 4 | 4/4 | 0/4 | 4/4 / 4/4 |
| c1m1: both | 3 | 3/3 | 0/3 | 3/3 / 3/3 |

These are **11 pairs / 22 runs from four source tasks**, selected after the stop because both arms were valid and finished. The original plan was 36 cells / 18 pairs / six sources; 24 cells were observed, 23 were valid, one was invalid, and 12 never started. The invalid `strollers/c1m1/B` cell and its valid successful A partner are both excluded from this paired description. The registered primary remains `not-measurable`, with null numerator and denominator. No further U8n live run is planned under the user's latest instruction.

B's actual-delivery task-oracle pass count remains 0/11 because `final_text` was empty; its candidate-oracle 11/11 is an auxiliary diagnosis, not a replacement reward. Native recovered requires the first negative judgment, consumed feedback and successful task reward—not merely a corrected candidate. False completion was 0/11 in both arms, but B had zero final approvals, so that zero cannot establish approval precision. B consumed the nonfinal feedback in all 11 runs and replanned twice per run. Its 22 repeated rejections of supported candidates are within-run observations, not 22 independent cases.

The direct conclusion is **over-rejection of repaired, supported candidates prevented delivery in this observed Noul configuration**. Execution order and the infrastructure stop selected the available sample. No CI, non-inferiority claim, causal repair-effect estimate or population generalization is supplied. The later evidence-capture code repair does not alter these original results.

## Verifier defects and responses

The runtime judge that permits answer delivery, the native verifier that records strict task success, and the validator that accepts output shape/numerics have different roles. Their failures should not be collapsed into one broken-verifier explanation.

**I5 task-contract delivery.** The source6 task required clarification for multiple orders in one item. Preserved judge feedback instead demanded answers for both orders. Code inspection found that the judge input omitted the task system override. Same-request tool evidence was also described ambiguously relative to retained evidence from an earlier request. These are defects in the information given to the final judge. The full ephemeral judge request was not retained, so the audit did not reconstruct every transmitted byte or isolate one wording change.

I5 completed six valid runs but delivered no strict successes: A 0/3, B 0/3. All were held by verification, within the 540-second root budget. Helper intent was A 36/36 and B 35/36; target accuracy was 36/36 for both. A recorded candidate was not a delivered answer, and the common hold cannot be attributed to the Jev helper alone.

Source7 passed the task contract to the judge and clarified same-request versus retained evidence. A new freeze and admission preceded I6. On the three known inboxes, both arms then delivered 3/3 strict successes, with 36/36 intent and target items. This is follow-up behavior consistent with the repair. It is a separate source/account lineage and nondeterministic rollout, not an isolated causal estimate. I5 0/6 remains intact; I6 6/6 is not pooled with it.

**U4/X2 numerical boundary rejection and measured correction.** Binary floating-point error caused permitted boundary outputs to be rejected. The common SystemOne and matched Astra probability-sum checks were corrected without widening tolerance. The [full-matrix post-hoc analysis](corrections/numeric-parser-20260928/README.md) checked all 1,920 cells, reparsed all 640 Jev and 640 Astra pointwise responses, and retained 640 native Astra listwise choices whose raw provider bodies were unavailable. It first reproduced the original outcomes, summary and CI exactly, then recomputed with the same grades, clusters, seeds and 2,000 resamples. All 24 original files remained unchanged.

All five boundary rejections were newly admitted, but only one U4 pool and two X2 pools gained a correct selected candidate. Corrected Jev accuracy is **59/80 for U4 and 196/240 for X2**. The U4 `not-supported` decision and X2 `mixed`/unproven non-inferiority remain. Substantial selection loss persists after correcting the validator. This is a post-hoc correction of retained responses, not a new model experiment or replacement of the original preregistered result.

### Historical results and the earlier impact bound

The original [U4 result](evidence/panel/jev-panel-r5/u4/results.json) was 58/80 vs 79/80, Δ −26.25 pp, CI [−36.14, −17.28]; the original [X2 result](evidence/panel/jev-panel-r7/x2/results.json) was 194/240 vs 226/240, Δ −13.33 pp, CI [−17.92, −8.87]. Before actual rescoring, the shadow audit bounded possible gains at 2.50 pp and 1.25 pp. Measured gains are now 1.25 pp and 0.83 pp, respectively. The [fix record](study/audits/numeric-tolerance-fix/closure.json), [shadow comparison](study/audits/numeric-tolerance-fix/shadow-parser.json) and [historical upper bound](study/audits/numeric-tolerance-fix/impact-upper-bounds.json) remain available.

**Infrastructure and unexecuted work.** E6 retained 19 valid successes, two invalid cells and 15 unstarted cells; E7 does not erase them. Earlier 180-second interruptions and later 540-second conditions are separate executions. In the original lineage, U0e's valid semantic failure left U8n's prerequisite unmet, so its 36 planned runs were unexecuted, not a measured 0% success rate. Source7/E8 subsequently passed admission and produced the interrupted observations described above. Its one invalid cell failed the injection-evidence contract and is not counted as a semantic Noul failure; the earlier prerequisite-failed lineage remains unchanged. No further U8n live run is planned, and the post-hoc complete-pair findings do not shrink the original denominator. These cases must not be used to explain away the measured Noul/Score accuracy losses.

## Operational implication

Prioritize bounded intent classification for new-source validation; do not substitute Noul/Score wholesale in the tested configurations. For Choice, resolve uncertainty about acceptable loss. For C, test tasks that actually exercise escalation under a newly frozen policy and cost/latency contract. Repeating saturated successes will not answer that question.

The 120-pair U3 latency result supports faster judgment responses: median paired difference −10.20 seconds, 95% CI [−11.34, −8.81]. It is not an end-to-end time or invoice-saving estimate. A report, replay, hash check or completed publication is likewise not an additional task-success observation.

## Evidence navigation

- [Registered unit and lineage index](units.json): native result, analysis and denominator pointers for the 27 registered units.
- [Panel disclosure and recomputation scope](PANEL-DATA.md) and [source-to-public digest map](evidence/panel-source-map.json). Public projection digests and original native digests are distinct.
- [Measured U4/X2 correction](corrections/numeric-parser-20260928/README.md) and [execution/preservation receipt](corrections/numeric-parser-20260928/receipt.json).
- [I5 failure audit](study/audits/i5-natural-audit/audit.json), [I6 follow-up audit](study/audits/i6-natural-audit/audit.json), and [E6 interruption diagnosis](study/audits/e6-u7r0-diagnosis/diagnosis.json).
- [E8 U8n observed-pair analysis](analyses/u8n-observed-pairs-20260928/README.md), [original E8 U8n result](evidence/e2e/jev-verdict-e2e-r8/u8n/results.json), and [additive E8 disclosure map](evidence/e2e-source-map-e8.json). Candidate diagnostics and native completion remain separate.
- [Numeric-boundary code validation](study/audits/numeric-tolerance-fix/validation.json), separate from the measured correction.

The packet was merged into `main` by [PR #46](https://github.com/mangowhoiscloud/geode-eval-artifacts/pull/46) (merge commit `3bcf4044`) and is publicly readable on GitHub. This report interprets retained analyses and the explicitly labeled correction; it is not an exhaustive semantic revalidation of raw gold.
