# G-code candidate ratchet

This is an unfrozen r3 candidate-only development experiment. No helper launches
Harbor or calls a model. Source placeholders are deliberately non-runnable.
The target is five fresh valid passes, with prospective stop on the first valid
zero or invalid evidence. It is not best-of-five selection or a held-out set.
Historical raw data, scores, failed attempts and full-suite eligibility stay unchanged.

## Fixed execution

- Up to five distinct jobs: candidate-r1 through candidate-r5, one trial each.
- Full `GeodeRuntimeHarborAgent`, verify_mode reflexion, OpenAI subscription
  gpt-5.6-sol, root effort max. Worker difficulty, explicit worker effort,
  wrap-up and judge effort follow the exact bundled source. Do not call every
  model invocation max or assume every judge/auxiliary call has complete usage.
- Fresh Harbor container and isolated GEODE home per trial, no outer search.
- Concurrency 1; Harbor retries 0; canonical task/image/verifier unchanged.
- Each G-code trial: agent 900 seconds, verifier 900 seconds, build 600 seconds,
  1 CPU, 2048 MB RAM, 10240 MB storage, no GPU. Setup 360 seconds and bounded
  finalization 20 seconds follow the pinned runtime/Harbor implementation.
- Candidate budget: at most 4500 agent-seconds. No paid shell canary is
  authorized. The first G-code trial is the sequential development gate.
  Fresh no-model install-only, shell oracle and G-code oracle checks remain
  mandatory; the shell fixture exists only for those no-model checks.
- Admission `passed` means evidence validity, not semantic success. A valid
  semantic zero or canonical timeout zero stays valid, selected, and admitted;
  the separate continuation condition stops new calls. Infrastructure/evidence
  invalidity also stops calls. No replacement or extra repetition is granted.
- Never pool across source candidates: neither r1 nor r2 contributes passes here.
- Exact 5/5 is a development acceptance threshold only. It cannot establish
  native Codex superiority, causal improvement, generalization or suite repair.

## Required operator receipt

Before preparation, create a source-bound local gate JSON under this run. Use
an input filename other than the helper-owned `preflight/local-gates.json`.
Required keys are `source_revision` (full committed HEAD), `passed: true`,
`model_calls: 0`, `checks` and `evidence_hashes`.

`checks` must contain `lint-format`, `type-check`, and `targeted-tests`. Each
value has the actual `command`, `exit_code: 0`, and run-relative `log_path`.
Every log path must have its actual SHA-256 in `evidence_hashes`. Include
additional helper/cancellation/observability regression commands as checks.
No fabricated exit codes, copied historical logs or omitted failed checks.

Source must be a clean exact commit; helper artifacts are ignored derivatives.
CI is optional before this user-authorized development run. If supplied, its
headRefOid must match source and no known failed check is accepted. Pending CI
is not called green. Eventual PR/required-CI GitFlow gates remain mandatory.

## Commands (replace symbolic arguments with exact paths)

Run from the candidate worktree, never the historical checkout. Pin Harbor:
the existing historical virtualenv contains 0.8.0, which is not supported by
this full-runtime adapter. A 0.22.0 offline overlay is available on this host.

```text
uv run --offline --with harbor==0.22.0 python -B NEW_RUN/candidate.py self-check
uv run --offline --with harbor==0.22.0 python -B NEW_RUN/candidate.py prepare --source-revision EXACT_COMMIT --local-gates SOURCE_LOCAL_GATES_JSON --canonical-run CANONICAL_FIXTURE_RUN
TZ=UTC uv run --offline --with harbor==0.22.0 harbor run --config NEW_RUN/preflight/job-install-shell.json
TZ=UTC uv run --offline --with harbor==0.22.0 harbor run --config NEW_RUN/preflight/job-oracle-shell.json
TZ=UTC uv run --offline --with harbor==0.22.0 harbor run --config NEW_RUN/preflight/job-oracle-gcode.json
uv run --offline --with harbor==0.22.0 python -B NEW_RUN/candidate.py freeze
uv run python scripts/eval/contract.py validate-run-spec NEW_RUN/run-spec.json
```

The three no-model commands need private logs from process start, exactly
`preflight/install-shell.operator.log`, `oracle-shell.operator.log` and
`oracle-gcode.operator.log`. Set TZ=UTC on the actual processes, not only the
report. A failed/incomplete oracle or install prevents freeze and all calls.
The helper never overwrites an existing preparation or freeze.

For candidate-r1 through candidate-r5, stopping after the first valid zero or invalidity:

```text
TZ=UTC CODEX_FORCE_AUTH_JSON=1 uv run --offline --with harbor==0.22.0 python -B NEW_RUN/candidate.py check --job JOB
TZ=UTC CODEX_FORCE_AUTH_JSON=1 uv run --offline --with harbor==0.22.0 harbor run --config NEW_RUN/job-JOB.json
uv run --offline --with harbor==0.22.0 python -B NEW_RUN/candidate.py admit --job JOB --write
```

Set CODEX_FORCE_AUTH_JSON only in the Harbor process environment, never
agent.env. Check reads auth only after frozen evidence/source/order checks;
it emits no credential/account identity. Credential headroom is at least
2400 seconds per next trial; live response identity proves route entitlement.
Recheck before each repetition, not just at the beginning of all five.

Preserve each actual process with an observer-side `script -q -r -F` capture
and a separate operator log. Store both under `recording/JOB.*`; use a KST
timestamp in the filename and UTC as the canonical process/event timezone.
Closure requires exactly one nonempty `JOB.*.typescript` and one nonempty
`JOB.*.operator.log` per observed job. Missing procedure evidence blocks artifact
closure; it does not change a valid task result into an invalid attempt or zero.
Observer capture is procedure evidence, never raw Harbor trial capture or a
score authority. Wait on process/container/native result state; do not restart
a healthy job. Read the final whole log after closure and archive before cleanup.

Close after all five jobs or after the first valid zero/invalid admission stops expansion:

```text
uv run --offline --with harbor==0.22.0 python -B NEW_RUN/candidate.py close
uv run --offline --with harbor==0.22.0 python -B NEW_RUN/candidate.py close --write
uv run python scripts/eval/contract.py validate-run-bundle NEW_RUN/run-spec.json
```

Closing is exclusive, not a status snapshot. A first valid zero fails the
development continuation gate, but current v1 cannot encode a partial all-valid
cohort with a null primary. Such a stop preserves real attempts/outcomes and
explicitly omits analysis; it does not fabricate invalidity or shrink five.
An actual invalid selected trial permits a not-measurable primary under v1.
Use validate-run-bundle only when closure reports analysis_emitted=true.
Unexpected live job names, missing earlier jobs, a sixth candidate, or any job
started after prior invalidity or a valid selected zero blocks closure. Preserve such raw
evidence for an explicit protocol-violation audit instead of silently dropping it.

## Development question and prior candidate

This candidate examines independent-evidence-first neutral Reflexion,
root-model inheritance when an agent model is omitted, and a bounded receipt
of actual Codex image dispatch. The source revision remains a placeholder
until a reviewed, committed candidate and its local gate receipts exist.
These planned changes are not a claim that the draft has already executed
or that a receipt proves model attention, understanding or successful repair.

The separate r2 candidate stopped after original valid selected rewards
[1,0], leaving three of five planned attempts unexecuted. Its development
gate failed. Canonical closure and publication remain blocked by custody
incident 001: the first trial's source SHM changed during our direct
`sqlite3 -readonly` audit after admission. No original-byte replacement or
hash substitution was accepted. The incident SHA-256 is
`7bfa44acfd98d45b834e05e408eb70127f478570fa3605593c9543bba9bbfef3`.
Exact original admission, spec and helper hashes are recorded in
source-provenance.json. No r2 analysis exists or is inherited; no prior result
is copied, selected, pooled or reclassified by r3.

## Dispatch coverage acceptance

Before prepare/freeze, the root must review the committed receipt producer
and local gate evidence. The existing receipt type is
`core.observability.activity.LLMRequestImageReceiptDetails`: `scope`,
`image_count`, `encoded_image_bytes`, `complete`, `rows_omitted`, and bounded
`refs` with `call_sha256` and `sha256`. No new schema or raw store is added.
Only candidate.py changes prospectively; reused-evidence.py and its original
function provenance stay unchanged.

For a dispatch-coverage finding, require a completed judge call matched by
its existing session/turn/step/call/attempt identity to the corresponding
actual serialized Codex input metadata. Keep these three boundaries distinct:

- `_judge_messages` reports selection from retained observations.
- Context-overflow and middleware may change the subsequent request.
- Only metadata measured after Codex conversion describes actual serialized
  `input_image` blocks. It does not prove provider attention or interpretation.

Retain bounded metadata through the existing private hook record and native
DB, with original DB/WAL/SHM hashes binding custody. Do not log raw prompts,
image bytes, solutions or provider reasoning, and do not create another store.
The prospective `completed_codex_request_image_receipts` check requires every
successful completed `codex-oauth` call's `payload.request_image_receipt` to
validate against that existing type. Missing/malformed required receipts are
evidence invalidity; the raw Harbor reward stays untouched. Admission telemetry
`request_image_dispatch.calls` retains only row ID, llm_attempt_id and the
validated receipt. It reuses the same copied snapshot as geode_checks; it does
not open the source DB a second time.

Failed/cancelled calls without a successful result remain explicitly unknown,
not image zero. With no completed Codex calls the dispatch observation is
not-measurable; existing source/model-route and canonical-timeout rules still
decide admission. Do not require positive image count or complete=true:
well-formed partial receipts with explicit omissions are admissible.

Inspect a source DB only through `read_closed_hooks`, after native writers
have closed. That existing helper copies DB/WAL to a temporary snapshot,
binds original source hashes and discards the copied index. Never open the
source database directly, even with `sqlite3 -readonly`, `mode=ro` or
another nominally read-only client. If any admission-bound byte changes,
preserve it and block canonical closure/publication pending a factual
custody investigation; do not waive its hash.

## Evidence and guard boundaries

Admission reuses exact source-selected prior evidence functions, not a second
raw store. `source-provenance.json` binds original helper and function hashes;
`reused-evidence.py` contains no historical writer. Numeric reward equality
uses finite binary equivalence before this new freeze (1 equals 1.0, bool and
non-finite values fail). No hash-bypass correction is inherited. The existing numeric-equivalence function retains its original source provenance.
Canonical attempt IDs are lowercased at emission, with uniqueness enforced;
case-sensitive native trial paths and all original evidence remain unchanged.

Require exact job/trial/task/source identity; complete private trajectory scope
and replay; valid Harbor ATIF; runtime-finalized exports; matching DB/WAL and
runtime_event_refs; paired durable LLM starts/ends and observed expected route.
The candidate-specific route wrapper rejects typed OpenAI AuthenticationError
and PermissionDeniedError even when another root/worker call succeeded. It
does not reclassify recovered transient errors merely because they occurred.
Read SQLite only after job/trial/runtime writers are closed, through the existing
temporary DB/WAL-copy reader; never open the source DB directly, and emit no
raw reasoning, tool text, account identity or credentials.

Do not require a positive cache hit to call a trial valid. Preserve explicit
zero, missing fields, observed sums and missing counts independently. A paired
cancelled LLM attempt may have no provider usage; unknown totals stay null.
The current scope remains recorded AgenticLoop attempts, whole-runtime complete
false and subscription billing unknown. Judge invocation is not proof that a
rejection/hint was consumed and repaired; report that evidence separately.

At closure the current run-spec/attempt/analysis schemas and existing
geode.trajectory@1 reference view are validated with the repository validators.
Per-trial originals remain replay authority. Raw trajectory/session/PTY content
is private; publication needs separate exact-byte secret/PII/path scans and
append-only remote readback. These helpers never publish, commit, release,
tag, install globally, restart services or modify another worktree/container.
