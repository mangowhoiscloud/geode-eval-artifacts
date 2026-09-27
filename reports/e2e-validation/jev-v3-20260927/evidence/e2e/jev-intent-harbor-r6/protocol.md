# I6 source7 current preparation authority

This new lineage is OFFLINE PREPARED, ACCOUNT UNBOUND, NOT FROZEN, NOT EXECUTED.
The current appendix at the end supersedes historical I5 readiness and budget
wording below. Earlier preparation text is retained only as provenance.

# Intent and target handoff: Harbor preparation

Status: runnable preparation; source/collector review pending. No inference, run freeze, publication, or adoption is authorized by this file. Parent source/spec review precedes freezing and the separate live admission. The local runner exposes gated execution commands for that later approval; adding them is not an execution receipt.

## Question and comparison

Can a Jev intent-and-target helper preserve verified whole-inbox completion while changing helper latency, root correction burden, and total recorded consumption, compared with a typed Astra helper?

A uses subscription `gpt-6-astra` / `xhigh` for `analyze_request`. B uses direct `jev-1.13.0` for that same tool. Both return the same selected intent and source-bound target projection. Native Jev probabilities remain in private evidence, outside root context. Both roots, all round reflections, and final semantic verification use subscription Astra / xhigh. Global judgment engine remains `llm`. This is the task-scoped `DecisionHandoffTool`, not GEODE's deterministic task preflight or a new general intent router.

The historical Harbor argument `verify_mode=rule_based` is required by the current handoff constructor but resolves to mandatory `LLM_JUDGE` in current source. Both raw and effective meanings must remain visible. Validate actual `turn_verification` and `cognitive_reflection` call purposes, model, source, effort, usage, and consumers; a configuration label is not successful judgment evidence.

## Fixed workload and order

Reuse the complete existing `decision-handoff-inbox.json` fixture without rewriting requests or gold labels. It is author-visible synthetic material, not held-out data.

| Phase | Order | Size |
| --- | --- | --- |
| Admission | `inbox-admission` A then B | 2 items per arm; excluded from the primary metric |
| Natural | `inbox-explicit` A/B; `inbox-context` B/A; `inbox-korean` A/B | 3 inboxes × 12 items × 2 arms, one repetition |

There are 36 item observations and 72 intended Choice answers per arm when each inbox is interpreted once; actual repeated calls/answers are reported separately. The three inboxes, not the 72 answers, are the primary units. Original requests, candidate inventories, criteria and task policy match within each pair. Independent root rollouts may produce different downstream inputs and call counts.

Examples already in the fixture include explicit lookups; cancel/refund requests; negated and quoted old commands; corrected or missing targets; multi-target requests; and an undecided cancel/refund request. The sandbox offers `analyze_request` and `lookup_order_status` only. Write requests are correctly reported as unsupported; this experiment does not establish successful mutations or general multi-intent execution. Labels and confidence never grant permission.

## Consumption and scoring

The actual chain is helper `structured_decision` → `analyze_request` result → subsequent root request consuming that tool-call ID → root-selected lookup, clarification or unsupported answer → common final verifier → offline Harbor oracle. `HandoffReceipt` and the existing oracle join tool-result IDs and consumed lookup evidence. A same-batch helper and lookup cannot establish consumption.

The collector is called explicitly with `expected_effective_verify_mode="llm_judge"`. Its current-source native/source-DB proof must admit the actual final call, not only the legacy `rule_based` argument. Freeze/preflight fail closed if that collector API is absent. Ordinary helper runs do not produce the matched-verifier-only `verification.json`: final observations come from `handoff.json` verification requests, the runtime's `native_verify`, canonical call/usage events, and source DB. Each observed tool batch must have an actual reflection request before the next ordinary root/final request; a missing round/final request leaves this comparison's coverage incomplete. Projection records actual `llm_call_id` consumers for every tool result, not an invented step identifier.

Primary `strict_task_success_delta`: `(B strict inbox successes - A strict inbox successes) / 3`. Strict success requires canonical `passed`, native reward, final verification and complete consumption, plus `wrong_target_lookup_count == 0`, `extra_lookup_count == 0`, and `false_completion_count == 0`. Canonical `passed` and native reward remain separate, unchanged fields. The existing oracle allows a corrected extra read; the strict analysis records this distinction without rewriting native reward. Report initial/final intent and target accuracy separately, along with wrong/extra/rejected lookups, false completion, repeated helper calls/items, helper corrections, root and reflection calls, final verification attempts, runtime and host elapsed time. An incorrect helper label can coexist with correct final work when the root corrects its interpretation.

Valid semantic failures stay failures. Any invalid/incomplete planned cell makes the primary result not measurable with null counts. Preserve native failures and partial consumption. No automatic trial rerun, no intervention injection, no A0 arm. This is a diagnostic with no adoption/release authority.

In `results.json`, an unmeasurable primary has null value/numerator/denominator. The repository's `analysis.json` schema represents that same state as `value="not-measurable"` with null counts. A root that omits the required helper is a semantic failure; unobserved helper labels stay null instead of being manufactured or counted as valid predictions.

## Environment, bounds and accounting

Pin clean source through this run folder's one-time `source-pin.json` (fixed checkout path and 40-hex revision), then the source archive, task checksums, oracle bytes, `uv.lock`, Harbor 0.22.0 and existing Docker image digest. Use a fresh public-network agent container and separate offline verifier per cell; no operator workspace mount. Root: 6 rounds / 540 seconds shared across initial and at most two verification continuations; Harbor agent: 570 seconds; setup: 600 seconds; verifier: 30 seconds; host watchdog: 1290 seconds; cleanup: 120 seconds. Keep native bounded root retry policy identical, helper dispatch once per invocation, no trial retry. Dollar/token cap remains unset; bounded workload and timeouts remain.

Use existing observer call/attempt IDs and canonical usage presence fields. Preserve zero versus missing input/output/cache/reasoning tokens, usage on failed completed calls, and incomplete coverage. Show root/helper/cognitive/final purpose totals and total recorded task use. TypeSafe input tariff is $0.042/M input tokens with no output fee, checked against https://docs.typesafe.ai/models on 2026-09-24. Provider-reported actual charges remain null unless the provider supplies them; Astra API-equivalent and Jev tariff calculations are distinct estimates, never invoices. The source-owned Astra reference dated 2026-09-21 ($10/M input, $50/M output) stays a pinned reference estimate, not a claim about current tariff or subscription billing. Preserve pricing reference date and source rather than silently updating historical evidence.

Timing joins `call_accounting.llm_attempt_id` to the terminal `call-events.json` `payload.duration_ms` (the persisted projection of the observer's `latency_ms`) and converts milliseconds to seconds; helper tool duration comes from `handoff.json.elapsed_seconds` with its `tool_call_id`. Retain failed/invalid trial observations too. Summarize per-purpose attempt time and inclusive helper tool time separately: the helper contains its decision call, so these overlapping durations must not be added together. Runtime and host wall time are separate measurements. Missing, non-numeric, nonfinite, zero or negative (≤ 0) values and duplicate identities yield null duration, not zero or duplicate consumption; activity rows before schema v12 stored an unobserved latency as 0.0. Incomplete runs or timing coverage retain observed sums/medians and counts while complete totals/medians remain null.

## Evidence and replay

Every cell retains native Harbor result/reward, independent verifier receipt, handoff result/receipt, canonical session/call events, full-private and digest-policy normalized GEODE trajectories, ATIF, recording.cast and recording receipt, cleanup, exact source hashes, append-only attempts and digest-bound analysis. Preserve invalid evidence too.

Preselect the `inbox-korean` A/B pair before results. Keep all six cells in the appendix/manifest. Reuse ATIF → agg 1× (idle cap disabled) → FFmpeg and the existing full-width LLM | Jev composition. No raw PTY claim, no synthetic thought process, no timestamps moved to fit captions. Presentation allowlist joins helper call → selected intent/target → consuming root call → actual lookup/disposition → oracle; it excludes system prompts, native reasoning and credentials. Exact-byte privacy review and playback play/pause/mid/end receipt precede film incorporation. Old recovery captions require a new intent observation projection; they cannot be relabeled as intent evidence.

## Reused execution path and entry points

Use `withheld-local-path-be6396699e82c889 -B runner.py` from this private run directory. The digest-pinned r6 `trial_config`, `child`, serial `dispatch`, key lifetime, watchdog, cleanup, replay checks and evidence writer remain the execution owner. This runner replaces only the study-specific schedule, gates, collector keyword adapter, item/consumer projection and aggregation. It never calls the old 54-cell scheduler or A0/18-denominator analysis.

1. After the source fix lands, the parent pins the clean fixed revision once: `--pin-source --source <clean checkout> --revision <40-hex SHA>`. It checks that the path is the checkout top level, `git rev-parse HEAD` equals the SHA and the tree is clean, then exclusive-creates `source-pin.json` (`geode.jev-runner-source-pin@1`: source, revision, created_at UTC) and refuses to overwrite it. Every other mode and each dispatched `--child` reads this pin before importing source and fails closed without it; freeze binds its digest.
2. `--self-test`: disposable, network-denied unit fixtures; no source archive, Docker, credential read, actual freeze or model. Exercises strict/native separation, invalid/incomplete primary, real collector keyword wiring, helper-consumer IDs, missing round/final observations, attempt/analysis schemas with every attempt selected, source-pin fail-closed and no-overwrite gates, `duration_ms` timing identity/null/non-positive/duplicate handling, and rejection of natural freeze before any write when admission/playback is incomplete.
3. `--prepare`, then `--self-check`. These create a fresh source archive/task bundle and provider-free oracle receipts. Outputs are exclusive-create; a failure is retained, never overwritten as a retry.
4. With parent infrastructure approval: `--infra-preflight --reviewed`. Only owned public agent/offline verifier lifecycles and cleanup; no model. Proof is bound to source, runner, manifest and Docker daemon and expires after 24 hours.
5. With source/spec/live approval: `--phase admission --freeze --reviewed`, then `--phase admission --preflight`, then `--phase admission --execute --reviewed`. Collection/analysis run serially inside the pinned dispatcher. The source DB, full/private and normalized trajectories, canonical attempt accounting, native verifier/reward and ATIF replay must all admit. First invalid cell stops dispatch; semantic failures continue.
6. Review both admission replays and write `admission/playback-check.json` with `played=true`, `score_authority=false`, source revision, admission results digest, mode (`ATIF-derived-player` or `ATIF-derived-MP4`) and exactly two relative cast paths/digests. The runner does not fabricate this human playback receipt.
7. Only after both admission arms pass and playback is approved: `--phase natural --freeze --reviewed`, `--phase natural --preflight`, `--phase natural --execute --reviewed`. Both freeze (before any write) and execution preflight enforce the admission/playback gate. The same immutable source and task inputs apply. No rerun/resume command exists; interrupted evidence needs an explicitly approved new lineage.

Internal `--child` is used by the pinned serial dispatcher. It reads the same `source-pin.json` from this run folder and rechecks the approved frozen phase before any account/key path. Every executed cell, including an invalid one, and the aggregate row stay `selected_for_analysis=true`. No execution command has been invoked during preparation. The selected representative pair stays `inbox-korean` repetition 0, A left/B right; all six natural rows remain in results and evidence manifests.


## Paired E-track slots (05 v2.2 §2.4-§2.6; 2026-09-27)

`--execute` no longer uses the serial r6 dispatch loop. The phase's rows of `e2e-slots.jsonl` (U0c-s01; U6b-s01..s03) are loaded with the verdict E2E runner's `paired_dispatch.PairedDispatcher` and must equal the prepared order (explicit A/B, context B/A, korean A/B). Both arms of a slot launch at once and the next slot starts after both are collected. The same guards run around every slot: the `e2e-slot` host lock, the Codex account, quota, the Jev ledger (arm b reserves the derived helper cap of 18 calls), a STOP file, and a frozen-input preflight. `paired_dispatch.py`, `run_guards.py` and `slot_guards.py` are byte-identical copies from `jev-verdict-e2e/`; freeze binds them and the slot matrix.

- Freeze adds these to every cell: the slot identity, `policy_digest`, `reset_digest`, `case_sha256`, `task_checksum`, `verifier_sha256` and `jev_call_cap`.
- Private receipts `<phase>/private-receipts/<attempt_id>.json` (0600) have the same columns as E2E. They also carry `helper_admitted`, `helper_fallback_used` and `helper_feedback_consumed`, which are null when not observed.
- Strict success (§3.1) is valid ∧ canonical pass (native reward, admitted final judgment, oracle consumption checks) ∧ zero wrong-target, extra lookups and false completions. It also needs `helper_admitted=true`, `helper_fallback_used=false` and `helper_feedback_consumed=true`, so a fallback never counts as helper success.
- `--infra-preflight` prebuilds all four task images, then proves two concurrent agent/verifier pairs.
- The I-r5 run_id preserves §2.2's base and adds the fresh lineage: `geode-jev-choice-intent-{admission|natural}-<date>-r5`. The run-spec has `max_concurrency` 2 and an Astra `budget.limit` of 10 per trial.


## I-r5 source6 recovery preparation (2026-09-27)

Status: unpinned file preparation only. The exact source6 revision is pending.
No source pin, source archive, source proof, offline proof, infrastructure proof,
freeze, model run, or human playback approval has been created for I5.

The 43-file I4 allowlist was copied byte-for-byte before changing only this
protocol, the runner's run-id suffix to r5, and manifest paths to I5. Payloads,
case files, instructions, orders, interventions, task timeouts and slot order
remain unchanged. Four copied task oracle files still contain their source5
bytes; they are not represented as source6-bound until the final source owner
SHA comparison and binding are completed.

The intended source6 includes both observation-quality provenance repair and
an independently tested numeric-boundary repair. The latter also affects the
I helper's existing 1e-5 validation boundary. Do not claim a behaviorally inert
source update. Preserve the numeric tolerance, prompts, metrics, workload,
models and effort; use a fresh same-source admission before natural execution.

Root 540 seconds, Harbor agent 570 seconds, watchdog 1290 seconds, setup 600,
verifier 30 and cleanup 120 remain unchanged. The 540-second allocation is one
global shared clock, not a measured SLO or 180 seconds guaranteed per turn.
Six root rounds and at most two verification continuations remain unchanged.

Source-independent proposed schedules exist for 2 admission and 6 natural
cells. Source-pending run-spec review drafts live only in the preparation
folder, with revision null and no readiness claim. Do not freeze them. After
source6 pinning, regenerate native proposed specs and source-bound proof via
the existing functions. Do not run --prepare over these copied inputs.

Natural requires I5's own complete, strict admission 2/2 and a new human
playback receipt tied to its exact results/source/casts. Prior I4 results and
playback approval do not apply. Original I4's four observed natural cells and
invalidated result remain preserved; I5 is a separate full six-cell cohort,
not a partial resume or replacement of original evidence.

The preparation receipt and remaining gates are recorded in
budget-recovery-20260927/i5-preparation/README.md.


## I-r5 source6 bound recovery preparation (2026-09-27)

Source: 68a1675733f24d897622d7d12286d52255fb485d at the clean detached
checkout withheld-local-path-dccd118251c54003 This new I5 lineage
binds its native source archive, manifest and four oracle copies to that source.
The runner differs from I4 only by its -r5 run-id suffix. Original I4 remains
immutable; none of its results, freezes, infrastructure or playback approvals
is adopted as an I5 outcome.

Payloads, case files, instructions, orders, interventions, task timeout and slot
order are unchanged. Root 540 seconds, Harbor agent 570 seconds, watchdog1290,
setup600, verifier30, cleanup120, six rounds and at most two verification
continuations remain fixed. The root allocation is one shared global clock,
not a measured SLO. Models and effort remain Astra xhigh and direct Jev1.13.0.
The source includes observation capture provenance, exact numeric-boundary and
content-hash compatibility repairs. The numeric repair can affect the existing
1e-5 helper acceptance boundary; no behaviorally inert source claim is made.

Admission is two fresh A/B cells and natural is the fixed full six-cell cohort:
explicit A/B, context B/A, Korean A/B, paired concurrency2, repetition0.
Natural requires I5's own complete valid strict admission2/2 and a review receipt
bound to the exact I5 source, admission results and both casts. Prior source5
playback does not transfer. The prospective delegated-review amendment and authorization are bound in the
appendix below before any phase freeze.
This preparation records no human playback, no delegated review completion and
no played=true receipt. Delegated review, when actually performed, must be
identified as delegated rather than human-watched.

The same-source strict2/2 gate and original primary/invalidity rules stay intact.
Source5 U6b's four observed cells remain separate, without pooling or retrospective
acceptance. Preselected Korean replay is not substituted after a failure.
Draft specs retain live_test_approved=false until the parent's native gate.

Do not run --prepare over the copied bundle. Native offline checks, source proof
and the final readiness receipt are in budget-recovery-20260927/i5-preparation.
New Docker infrastructure, live account/quota/cost checks, review authorization
binding and phase freezes/execution remain separate operational steps.

## Delegated review timing amendment bound before freeze

The original conditions above are retained as historical preparation text. The
source-bound appendix supersedes their unpinned readiness status. Only the human
review timing precondition is prospectively amended by the following authority;
same-source valid strict admission2/2 remains mandatory.

- withheld-local-path-c7cc289dffbbf546
  SHA-256: 3b5a7f0fa49160835e9f0d9a521fb08bb351392f8734434a905ac85679bda90b
- withheld-local-path-083958e6ea6a8e4b
  SHA-256: 3af3919606cd30d585fa10fceeef1623238cbdd15f0ac59dbea17f2928e8a026
- withheld-local-path-91375061977c4567
  SHA-256: 333e9792e97e4633c54ce408eb274fefa331a162324640f6eab10c3046cad46e

A delegated reviewer must actually operate the derived player: playback, pause,
seek and end verification, plus independent original-data/hash/analysis review.
Only the agent who performs those actions may issue played=true. The receipt
must bind exact source/results/casts/video and include review_authority=
delegated_agent, human_reviewed=false, human_review_status=
deferred_until_user_returns, score_authority=false, authorization, independent
review and player-observation receipt hashes. Rendering or frame extraction
alone cannot issue played=true. No review completion is recorded at preparation.
The user returning later may record human review separately. Frozen source5
results, model/effort, task/input/order, one repetition, six-cell natural cohort,
540/570/1290-second policy and primary/invalidity rules remain unchanged.


## I-r6 source7 prospective contract (current)

Source 1236ce96c8c5a79699d98f5c960b7a699c1f228a at withheld-local-path-f9e80ae4f1f321ed Same task payloads, requests, instructions,
orders, verifier bytes, model/effort, arm order and metric are retained.
The default judge now receives its already configured bounded/redacted task
instructions and distinguishes same-request prior observations from retained
context of earlier requests. This is a changed verification information
condition, not behavior-equivalent source maintenance.

Authority: withheld-local-path-bd3e9a5c47a0949d
SHA-256: 5528b6ffd52bed91e62cac3c5583dae5378588e7c980313caf3b43d8b1e5eebb
Adoption receipt: withheld-local-path-c353d28d7571ff76
SHA-256: 24e8ec2b51a67b54932a89065663fd190ce7a6aa8722f7847b02a560184af8e9
These prospectively replace the Astra hard-count wording of 05 sections2.2/4.3
for I6/E6 only. I5's actual75 over planned60 remains a protocol deviation,
with original native valid6/6 strict0/6 mixed unchanged and unpooled.

I6 admission2cells and natural6cells once, explicit A/B -> context B/A -> Korean
A/B, concurrency2, six rounds and at most two verification continuations,
root540/Harbor570/watchdog1290/setup600/verifier30/cleanup120 remain fixed.
The inherited budget.limit and planned_astra_call_cap names now mean operating
point forecasts: admission13 and natural75 Astra calls, not an enforced call
cap. Prior I5 observed A7+B6 and A39+B36 anchor these values. Conditional
stress288/864 is sensitivity only; helper multiplicity and context recovery
can exceed it. No runtime count cap or quota cadence change is introduced.
Both I6 phases are below planned300 and have no middle-slot quota read.
Account, STOP and preflight checks still run at every slot. Start projection
<=90 and observed used>=95 stop thresholds remain unchanged.

Account binding observed at 2026-09-27T21:08:53.048193+09:00: fingerprint anonymous-account-01, plan pro,
used0%, single primary window604800s/reset2026-10-04 08:12 KST.
Safe observation receipt: withheld-local-path-1afb2246a2c96cdd
SHA-256: c04413ec187ab26f728b4dd269858e764524fc1274d12613afa76905790a0b00
The new guard only is bound to this account. Prior guards and ledger rows are
unchanged. Actual account/window/reset are checked again before execution;
no old-account r is transferred. This does not assert infrastructure or freeze.
Native admission end_record supplies actual calls and the new-account r;
natural requires a finite same-epoch r and native90% start projection.
The current calibration filters account/plan but not window/reset, so safe
metadata sidecars must establish that boundary. Unknowns are not zero.

Natural requires I6's own source7 complete valid strict2/2 admission, independent
original-data/hash audit, actual derived-player playback/pause/seek/end and a
source7/results/casts-bound playback-check.json. Delegation authority above
remains applicable: review_authority=delegated_agent, human_reviewed=false,
human_review_status=deferred_until_user_returns, score_authority=false.
No played=true or human-review completion is created at preparation.
Old I5 admission or its actual player review does not transfer to I6.

U7 stays source5 in future E6; it is not changed by I6's source pin. Only valid
new-account quota calibration may be shared through the existing program ledger.
No old outcome is retroactively rescored. Do not run --prepare over copied
science inputs. Actual current steps and evidence are in D/i6-preparation.
