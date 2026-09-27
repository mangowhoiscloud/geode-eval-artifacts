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
- The I-r4 run_id preserves §2.2's base and adds the fresh lineage: `geode-jev-choice-intent-{admission|natural}-<date>-r4`. The run-spec has `max_concurrency` 2 and an Astra `budget.limit` of 10 per trial.


## I-r4 budget recovery preparation (2026-09-27)

This fresh lineage is pinned to clean source
`1f6553431932040336cadcddb26893e30ebbb706`. Case payloads, instructions, orders
and interventions are byte-preserved. Task agent metadata changes from 210 to 570
seconds. The new source archive, four oracle runtime copies, draft schedules/specs
and offline checks have been prepared from that source. Source proof binds the final
protocol and preparation bytes. Infrastructure proof, freeze and live execution
remain separate stages; no prior run result or approval is copied as a current
result. Do not run `--prepare` over these copied inputs: its exclusive-create task
writer is for an empty preparation. The companion
`budget-recovery-20260927/i4-preparation/README.md` records completed preparation
and the remaining infrastructure and execution gates.

The root 540-second budget is 180 inherited seconds times the existing maximum
three physical turns. It is an operational allocation, not a measured SLO or a
guarantee of 180 seconds per turn. All turns share one clock; rounds, continuation
count, model, effort, repetitions and workload stay unchanged. Budget hints and
reserve timing change with that value. The private `trial_config` wrapper updates
the actual legacy child's agent argument to 540 and Harbor override to 570; the
pinned legacy file stays byte-identical. Paired dispatch and account-margin checks
use watchdog 1290. Natural still requires this lineage's complete admission and
actual playback evidence. No previous approval or result is relabeled as current.
