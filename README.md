# GEODE Evaluation Artifacts

Raw run logs behind the benchmark numbers published in the GEODE docs
([Tau2](https://mangowhoiscloud.github.io/geode/docs/benchmarks/tau2) ·
[MCPMark](https://mangowhoiscloud.github.io/geode/docs/benchmarks/mcpmark)).
Every score GEODE publishes cites a result directory; this repository is where
those directories live, so any reported number can be traced back to verifier
output and the trace material retained by the producing harness. Trace fidelity
varies: tau2 and Petri retain full visible message sequences, while the public MCPMark
copy retains final answers and ordered MCP execution logs, not full model
dialogue. Hidden reasoning and local paths are removed from new public Petri
copies. See [`TRAJECTORIES.md`](TRAJECTORIES.md) for the stable schema,
redaction, admission, and retirement contract.

## Layout

| Path | Content | Producing harness |
|---|---|---|
| `TRAJECTORIES.md` | Stable `geode.trajectory@1` / `geode.trajectory-release@1` publication contract, legacy migration, redaction, validation, and deletion gates | repository policy |
| `reports/trajectory-inventory/` | Dated human- and machine-readable source inventories; current snapshot: [2026-07-21](reports/trajectory-inventory/2026-07-21.md) | cross-source audit |
| `mcpmark/results-geode-agentworld/` | MCPMark run directories. Per task: `meta.json` (route, timing, tokens, verifier result), `messages.json` (final answer or empty placeholder), `execution.log` when produced (ordered MCP actions/results), `summary.json` per run | `eval-sys/mcpmark@cd45b7f` + GEODE `BaseMCPAgent` adapter |
| `mcpmark/logs/`, `mcpmark/logs-cycle/` | Pipeline stdout logs (state duplication, verification, cleanup stages) | same |
| `tau2/simulations/` | tau2-bench simulation JSONs for GEODE-owned runs (`geode-*`, `crucible-*`, smoke variants) | `sierra-research/tau2-bench@1901a30` (`tau2==1.0.0`) + GEODE participant adapter |
| `crucible/runs/campaigns/` | Crucible (self-improving-loop measurement) campaign run state: per-attempt state, evaluations, gate outcomes | GEODE Crucible harness over tau2-bench |
| `crucible/runs/{row-cache,trajectory-snapshots}/` | Row cache and trajectory snapshots backing the campaign store (the local `gates/` store is currently empty; gate outcomes live inside each campaign's attempt state) | same |
| `crucible/gate-provenance/` | Gate provenance ledger: the frozen failure manifest, `cheaploop_v1` gate calibration, G1 trace-replay report, G2/G3a task sets | same |
| `sil/petri-audits/` | Petri adversarial safety-audit logs (Inspect `.eval` format, visible auditor/target/judge transcripts): the SIL fitness measurements. New public copies remove hidden reasoning and local paths. The [self-improving hub](https://mangowhoiscloud.github.io/geode/self-improving/) serves a curated 29-log subset with rendered views; this is the full set | GEODE `plugins/petri_audit` over Inspect |
| `sil/petri-dish/` | Sanitized Petri Dish audits of production agent scaffolds; kept separate from model-level GEODE Petri runs because the scaffold owns the prompt and native tool surface | Petri Dish over Inspect SWE / native ACP |
| `sil/audit-reports/` | Dated human-written analysis reports over the Petri audit runs (2026-05-10 onward, formerly `docs/audits/` in the main repo), plus their score matrices (`.csv`/`.json`) and delta charts (`.png`). The live `eval-logs/` manifest ledger and code-referenced docs stay in the main repo | GEODE `plugins/petri_audit` over Inspect |
| `reports/e2e-validation/` | Dated end-to-end feature-validation records (formerly `docs/e2e/` in the main repo) | manual validation sessions |
| `trajectories/` | Immutable normalized trajectory releases per the `TRAJECTORIES.md` contract: `<source>-<scope>-<published-utc>-<manifest-sha256-prefix>/` holding `trajectory.json` + `manifest.json` | per-release producing harness (named in each manifest) |
| `learning-views/` | Versioned `example -> rollout -> trajectory -> reward` projections with digest-bound native evaluator values; v2 keeps retry lineage and zero rewards explicit | GEODE evaluation data projector |
| `reports/checkpoint-retirement/` | Sanitized forensic receipts for retired local checkpoint stores; records integrity, aggregate schema statistics, runtime-consumer evidence, and disposition without publishing opaque state payloads | GEODE runtime-maintenance audit |
| `crucible/campaign-records/` | The G0-G7 era campaign record (EN/KO, formerly `docs/architecture/crucible.md` in the main repo): telecom v1-v72 measurement narrative, weakness band, S5 trial runs. Superseded as an architecture contract by `docs/architecture/crucible-kernel.md`; preserved here as the historical run record | GEODE Crucible harness over tau2-bench |
| `crucible/gate-provenance/crucible-power-admission-2026-07-13.md` | Family-power admission design record (Monte Carlo power audit of the frozen promotion rule; no provider calls) | GEODE Crucible harness |

## What was used

Everything below is also recorded per run inside the artifacts themselves;
this table is the summary of the stack that produced them.

| Component | Value |
|---|---|
| MCPMark harness | `eval-sys/mcpmark@cd45b7f` (MCPMark Verified release; standard = 127 pinned tasks), local Python 3.12 venv, official `pipeline.py` unpatched |
| GEODE entry point | `plugins/benchmark_harness/run_mcpmark.py` in the GEODE repo: registers the `geode` agent (a `BaseMCPAgent` wrapping GEODE's `AgenticLoop`) before `pipeline.main()` |
| MCP servers (MCPMark) | GitHub: `ghcr.io/github/github-mcp-server:v0.15.0` (Docker stdio) · Postgres: `postgres-mcp==0.3.0` via pipx · Playwright: `@playwright/mcp@0.0.68` (headless chromium) · Notion: `@notionhq/notion-mcp-server` (stdio) · Filesystem: upstream MCPMark default |
| tau2 harness | `sierra-research/tau2-bench@1901a30` (`tau2==1.0.0`), GEODE agent + GEODE user-simulator adapters; native `user_simulator` comparator runs labeled separately |
| Model routes | Primary historical route: `gpt-5.5`, provider `openai-codex`, source `subscription` (effort in run id: `xhigh`/`high`). The 2026-07-31 records use `gpt-5.6-sol` / subscription / `high`; the 2026-08-02 smoke and 2026-08-03 three-domain full cycle use `gpt-5.4` / subscription / `high` for both the agent and GEODE user. Comparators: `gpt-5.2` (subscription and PAYG, labeled in run id). Crucible train campaigns of 2026-07-11 through 2026-07-13 also used `gpt-5.4` but remain separately contract-scoped. Decoding parameters are not controllable on the subscription route; treat cross-paper comparisons as directional |
| Verifiers | Upstream per-task verify scripts (MCPMark) and tau2 reward/DB-state checks. No GEODE-authored judges |

## Run naming

- MCPMark: `geode-<model><effort>-<date>-<purpose>[-<slice>]`, e.g.
  `geode-gpt55-xhigh-20260704-mcpmark-verified-postgres`. `smoke-*` = single
  tasks from the `easy` suite; `verified-*` = the standard (Verified) suite;
  `notion-smoke-unblock*` = the 2026-07-10 session-expiry fix validation.
- tau2 simulations:
  `crucible-tau2-<gate>-<domain>-<candidate>-<agent route>-<user route>-n{N}k{K}[-suffix]`
  for Crucible probes (gate ∈ readiness/cheaploop/g2/g3a/g4), and
  `geode-<model>-<domain>-<scope>-<date>` for native GEODE runs.
- Crucible campaigns: `tau2-telecom-gpt54-train-<date>-r<N>` (r1-r35,
  2026-07-11 through 2026-07-13) plus `crucible-rowcache-live-*`
  cache-priming runs.

### 2026-08-11 GPT-5.6 effort surface

The [effort-surface record](reports/e2e-validation/2026-08-11-gpt56-luna-terra-sol-effort-surface.md)
measures every GEODE-exposed effort on GPT-5.6 Luna, Terra, and Sol through
the OpenAI subscription route. All 18 model-effort combinations preserved the
requested wire value and returned the exact response contract. The raw JSONL
retains six transient overload attempts and the same-combination recoveries;
the result is a routing/acceptance diagnostic, not a quality leaderboard.

### 2026-08-11 Codex / Hermes Petri Dish diagnostic

The [scaffold comparison](sil/audit-reports/2026-08-11-codex-hermes-petri-dish-scaffold-comparison.md)
uses a matched Petri Dish configuration for Codex CLI and Hermes Agent. Both
N=1 runs cleared the audit-quality gate and showed no concerning behavior;
37/38 judge dimensions matched. OpenClaw remains unscored because no validated
same-protocol adapter exists. This is a diagnostic, not a leaderboard.

### 2026-08-12 GPT-5.4 GEODE / Codex paired MCPMark diagnostic

The [paired run record](reports/e2e-validation/2026-08-12-mcpmark-geode-codex-gpt54-paired.md)
compares GEODE and Codex CLI on the same ten upstream `filesystem/easy`
tasks, GPT-5.4 subscription route, `high` effort, fixture reset, and exact
task verifier. Both arms scored **9/10** and failed the same trailing-LF case.
The two reviewed trajectory releases retain 486 canonical events and 166
exact tool pairs with zero orphans. Private bodies are digested, so all 20
records are scope-complete and intentionally replay-incomplete. This is a
paired harness diagnostic, not an MCPMark Verified leaderboard submission.

### 2026-08-13 GPT-5.4 filesystem/standard paired diagnostic

The [validated comparison bundle](mcpmark/results-paired/mcpmark-filesystem-standard-gpt54-high-geode-codex-k1-boundary-aligned-20260813/)
compares GEODE and Codex CLI on all 30 pinned `filesystem/standard` tasks with
GPT-5.4 subscription and `high` reasoning. GEODE scored **21/30 (70.0%)** and
Codex scored **20/30 (66.7%)** in one paired repetition. The two reviewed
trajectory releases preserve 3,381 canonical events and 1,430 exact tool
call/result pairs with zero orphans.

**Correction:** post-run source review found that the two adapters did not
implement the preregistered equal hard-wall timeout boundary. The original
prospective “supported” decision is superseded by the
[corrected analysis](mcpmark/results-paired/mcpmark-filesystem-standard-gpt54-high-geode-codex-k1-boundary-aligned-20260813/analysis.superseding-2026-08-13.json)
and its [digest-bound receipt](mcpmark/results-paired/mcpmark-filesystem-standard-gpt54-high-geode-codex-k1-boundary-aligned-20260813/correction.json).
The native 21/30 and 20/30 outcomes remain retrospective descriptive evidence
only. They do not support a matched-timeout, causal, efficiency, hypothesis,
or promotion claim. The exact runner is digest-bound but withheld, so the
public bundle is not independently executable by itself.

### 2026-08-14 GPT-5.4 MCP tool-result cap diagnostic

The [validated Gate 0B bundle](mcpmark/results-paired/mcpmark-gate0b-tool-cap-gpt54-high-20260813t142345z/)
runs the same five pinned MCPMark `filesystem/standard` large-result tasks for
three counterbalanced paired repetitions under a common 1,200-second deadline.
With GPT-5.4 subscription and `high` reasoning, `unlimited-0` passed **10/15**
and `guard-25000` passed **7/15**, a signed delta of **+3/15 = +0.20**. This
supports the frozen hypothesis only for this diagnostic slice;
`promotion_authority=none`, and it is not a full MCPMark Verified headline.

Exact observed fresh-input totals cover 13/15 attempts per arm:
**3,782,288** tokens for `guard-25000` and **2,202,725** for `unlimited-0`.
The four score-bearing `author_folders` deadline expirations emitted no native
token counts. Six reviewed releases retain 26 scope-complete,
replay-incomplete trajectories; four scope-incomplete timeout trajectories
remain withheld while their verifier outcomes remain in the primary score.
The prior infrastructure-invalid runner attempt is preserved as lineage and
contributes zero denominator.

### 2026-08-14 GPT-5.4 Gate 0C filesystem30 paired diagnostic

The [validated Gate 0C bundle](mcpmark/results-paired/mcpmark-gate0c-filesystem30-gpt54-high-20260813t190922z/)
compares GEODE and Codex CLI on the same 30 pinned `filesystem/standard` tasks
in one paired repetition under a common 1,200-second action deadline. GEODE
passed **23/30 (76.7%)** and Codex passed **21/30 (70.0%)**, a signed delta of
**+2/30 = +0.0667**. This is a direct diagnostic with
`promotion_authority=none`, not an MCPMark Verified headline.

The reviewed releases publish 29 GEODE and 30 Codex scope-complete,
replay-incomplete trajectories with 3,091 events and 1,281 exact tool pairs.
The bundle separately labels 644/678 native execution-log rows and 645/678
normalized trajectory call attempts; one explicit GEODE recovery projection
accounts for the difference. One score-bearing scope-incomplete GEODE
trajectory remains withheld while its verifier outcome stays in the primary
score.

### 2026-08-12 GPT-5.4 GEODE token-efficiency rerun

The [matched rerun record](reports/e2e-validation/2026-08-12-mcpmark-geode-gpt54-token-efficiency-rerun.md)
repeats the GEODE arm on the same ten `filesystem/easy` tasks after repairing
the model-facing MCP result boundary and multi-round prompt prefix. Accuracy
stayed **9/10**, while native input tokens fell **29.8%** and output tokens fell
**19.0%**. The reviewed release retains 188 canonical events and 54 exact tool
pairs with zero orphans. This is a single-trial matched diagnostic, not an
MCPMark Verified score or a billing claim.

### 2026-07-31 GPT-5.6 subscription benchmark

The [run record](reports/e2e-validation/2026-07-31-gpt56-benchmark.md)
publishes the first `gpt-5.6-sol` / `high` benchmark batch from GEODE
`edb74602b`: MCPMark filesystem/easy scored **9/10**, while tau2 mock and one
Telecom-small task each scored **0/1**. The failures are retained as behavior
evidence, not removed as infrastructure contamination.

- Raw MCPMark receipts:
  `mcpmark/results-geode-agentworld/geode-gpt56-sol-high-edb74602b-20260731-mcpmark-filesystem-easy/`
- Raw tau2 receipts:
  `tau2/simulations/geode-gpt56-sol-high-edb74602b-geode-user-*/`
- Normalized MCPMark trajectories:
  `trajectories/mcpmark-geode-gpt56-edb74602b-filesystem-easy-20260731T034305Z-b86f5071cbe0/`
- Normalized tau2 trajectories:
  `trajectories/tau2-geode-gpt56-edb74602b-mock-telecom-small-20260731T034305Z-4ec1c13434d1/`

### 2026-07-31 hook and session-record contract E2E

The
[`geode-agenticloop-hook-middleware-behavior-e2e-20260731T091808Z-d418e55ff8aa`](trajectories/geode-agenticloop-hook-middleware-behavior-e2e-20260731T091808Z-d418e55ff8aa/)
release is the first stable `geode.trajectory@1` publication. A live
`gpt-5.6-sol` / subscription / `high` run exercised all 13 public lifecycle
hooks and the four trusted middleware seams. Its 27-event normalized sidecar
has complete release scope, exact tool call/result pairing, and no missing
required turn identifiers.

The release is intentionally not byte-replay-complete: private prompt and
result bodies are replaced by digests. Its `geode.trajectory-release@1`
manifest records that admission, the scope-bound privacy attestation, and
zero findings across the public secret/identity scan. Runtime SQLite, WAL,
JSONL, checkpoints, usage and provider diagnostics remain outside this
repository.

### 2026-07-31 GEODE v1.0.11 release regression

The
[`v1.0.11` run record](reports/e2e-validation/2026-07-31-gpt56-v1011-benchmark.md)
repeats the same GPT-5.6 subscription slices against the released package.
MCPMark filesystem/easy improved from **9/10 to 10/10**. Tau2 mock remains
**0/1** on the exact optional-argument comparator, while the Telecom-small
case improved from **0/1 to 1/1**.

- Native MCPMark receipts:
  `mcpmark/results-geode-agentworld/geode-gpt56-sol-high-v1011-686ff372-20260731-mcpmark-filesystem-easy/`
- Native tau2 receipts:
  `tau2/simulations/geode-gpt56-sol-high-v1011-686ff372-geode-user-*/`
- Stable MCPMark trajectories:
  `trajectories/mcpmark-geode-gpt56-v1.0.11-686ff372-filesystem-easy-20260731T105713Z-82fe94b01a25/`
- Stable tau2 trajectories:
  `trajectories/tau2-geode-gpt56-v1.0.11-686ff372-mock-telecom-small-20260731T105713Z-a71155f7006c/`

The stable releases contain 368 canonical events with zero missing required
turn IDs and 87 exactly paired tool calls/results. Scope completeness is
12/12; replay completeness is intentionally 0/12 because private bodies are
digested rather than published.

### 2026-08-02 GPT-5.4 subscription Tau2 cycle

The [run record](reports/e2e-validation/2026-08-02-gpt54-tau2-benchmark.md)
repeats the latest release-regression Tau2 slices with `gpt-5.4`, OpenAI
subscription, effort `high`, for both the agent and GEODE simulated user.
`mock/create_task_1` scored **0/1** because the model again supplied optional
`description=""`; the fixed Telecom-small task scored **1/1** with every DB,
environment, and user-side roaming check passing. Both runs ended normally
without route or harness errors.

- Native receipts:
  `tau2/simulations/geode-gpt54-high-afaab52b-geode-user-*/`
- Stable trajectory release:
  `trajectories/tau2-geode-gpt54-afaab52b-mock-telecom-small-20260801T173245Z-2dc79cb569f0/`
- Manifest SHA-256:
  `2dc79cb569f03e5f44ce008b32fd8af86f8388ab04341ee8f91c74fdffb6aa6b`

The release contains 158 canonical events and 10 exact tool pairs with zero
missing IDs or orphan pairs. The receipts are diagnostic and unfrozen;
`promotion_authority` remains `none`.

### 2026-08-03 GPT-5.4 subscription Tau2 base full cycle

The [full-cycle record](reports/e2e-validation/2026-08-03-gpt54-tau2-full-cycle.md)
publishes all 278 base tasks at GEODE `22789ee2`: Airline **42/50**,
Retail **79/114**, and Telecom **79/114**, for **200/278 = 0.7194**.
The route remains `geode_agent + geode_user`, so it is a GEODE behavior
diagnostic rather than a native-user Tau2 leaderboard claim.

- Native receipt copies:
  `tau2/simulations/geode-gpt54-high-22789ee2-geode-user-*/`
- Stable trajectory release:
  `trajectories/tau2-geode-gpt54-22789ee2-geode-user-airline-retail-telecom-base-full-20260803T091257Z-13162f7bcff9/`
- Manifest SHA-256:
  `13162f7bcff9ade1194f41af06549f0b0f239847f59630d5223386e2ca6362b3`

The release exact-joins 556 final parent sessions to 51,985 canonical events
and 3,964 tool call/result pairs with zero orphans. Seven task-level transport
retries created 14 additional SQLite sessions outside the final trajectory
parent set; that execution-lineage boundary is disclosed rather than hidden
behind `scope_complete`.

### 2026-08-04 runtime-faithful Tau2 infrastructure diagnostic

The [diagnostic record](reports/e2e-validation/2026-08-04-gpt54-runtime-faithful-tau2-diagnostic.md)
preserves the first snapshot-v4 three-domain run at GEODE `f08e7d6f`. The
278-task schedule produced 179 reward-bearing rows and 99 infrastructure rows
after GPT-5.4 subscription quota exhaustion, so it has no aggregate score
authority and does not replace 200/278. Its normalized trajectories contain
22,971 events; Airline and Retail are scope-complete, while Telecom truthfully
retains six orphan calls and is rejected by the hardened verifier.

- Diagnostic companions:
  `crucible/runs/trajectory-snapshots/runtime-faithful-20260804/`
- Machine-readable ruling:
  `reports/e2e-validation/2026-08-04-gpt54-runtime-faithful-tau2-diagnostic.json`
- Privacy review:
  `reports/privacy-reviews/2026-08-04-geode-gpt54-runtime-faithful-tau2.json`

No stable `trajectories/` release was created because stable admission requires
`scope_complete=true`. Raw receipts and runtime stores remain private; their
digests stay bound by the published runtime profiles and trajectories.

### 2026-08-03 GEODE v1.0.12 GPT-5.4 post-release regression

The
[`v1.0.12` run record](reports/e2e-validation/2026-08-03-gpt54-v1012-post-release-benchmark.md)
pins the published release commit and repeats MCPMark filesystem/easy plus two
Tau2 diagnostic tasks through the GPT-5.4 subscription route. MCPMark scored
**9/10**; the Tau2 mock and Telecom-small tasks scored **0/1** with
`USER_STOP` and `MAX_STEPS`, respectively. The failures are preserved as
behavior evidence and do not replace the earlier **200/278** Tau2 full-cycle
authority.

- Native MCPMark receipts:
  `mcpmark/results-geode-agentworld/geode-gpt54-high-v1.0.12-f99cea63-20260803-mcpmark-filesystem-easy/`
- Native Tau2 receipts:
  `tau2/simulations/geode-gpt54-high-v1.0.12-f99cea63-geode-user-*/`
- Stable MCPMark trajectories:
  `trajectories/mcpmark-geode-gpt54-v1.0.12-f99cea63-filesystem-easy-20260803T104819Z-9636b39c16fb/`
- Stable Tau2 trajectories:
  `trajectories/tau2-geode-gpt54-v1.0.12-f99cea63-geode-user-mock-telecom-small-20260803T104819Z-fd524ce7a3cb/`

The two manifests contain 416 canonical events and 72 exact tool pairs with
zero orphans. All 12 trajectories are release-scope complete and intentionally
replay incomplete. Native/public digests are recorded independently wherever
local paths or synthetic benchmark identities were redacted.

### Crucible 2026-07-13 operations-hardening cases

| Runs | Outcome | Evidence value |
|---|---|---|
| r29-r33 | Five pre-verdict operational failures | Producer auth, frozen-assay drift, budget-trajectory termination, unsupported concurrency, and session reaping were caught before a score could be claimed. |
| r34 | `INVALID`, no verdict | Power and runtime admission passed, but the evaluator subprocess exited before judgment. The run records one producer call and no score. |
| r35 | `INVALID` verdict | A verdict-bearing measured attempt was vetoed for `task_coverage_incomplete` and `infrastructure_contamination`; `promotion_authority` remained `none`. |

## Quantitative summary

Counted directly from the files in this repository on 2026-08-03; recompute
any of it with `python3 scripts/stats.py`. Token figures are what the
artifacts record: the subscription route reports usage per call, but there
is no billing meaning behind `cost_usd`-style fields.

**MCPMark** (all task attempts across the 27 result directories, including
retries and superseded first attempts):

| Metric | Value |
|---|---:|
| Task attempts with results | 119 |
| Verifier PASS | 96 |
| Input tokens | 21,308,655 |
| Output tokens | 970,586 |
| Agent execution time | 40,440s (~11.2h) |

**tau2** (`tau2/simulations/`, GEODE-owned runs):

| Metric | Value |
|---|---:|
| Runs with `results.json` | 390 |
| Episodes simulated | 2,977 |
| Episodes with reward recorded | 2,650 (reward 1.0: 1,694 · below 1.0: 956) |
| Episodes without reward | 327 (aborted/diagnostic probes) |
| Tokens | not recorded in tau2 simulation JSONs; cost fields are zero on the subscription route |

**Crucible** (`crucible/runs/campaigns/`, the SIL measurement harness):

| Metric | Value |
|---|---:|
| Campaigns | 38 (train r1-r35 + 3 row-cache priming) |
| Mutation attempts | 42 |
| Attempts reaching a verdict | 16 (the rest aborted before judgment) |
| Verdict-attributed usage | 5,115 calls · 44,216,109 tokens · 34,373s wall |

**SIL** (`sil/petri-audits/` plus promotion outcomes read from the same 16
verdicts: the self-improving loop's measurement and selection record):

| Metric | Value |
|---|---:|
| Petri audit logs published | 411 (`.eval`, 2026-05-15 to 2026-08-11) |
| Served in the self-improving hub | 29 (curated subset with rendered views) |

| Metric | Value |
|---|---:|
| KEEP | 1 |
| REJECT | 8 |
| INVALID | 7 |
| Promoted to core (`promotion_authority`) | 0; every verdict carries `promotion_authority: none` |
| Rejection/invalidation reasons | `infrastructure_contamination` 7 · `improvement_below_materiality` 4 · `confidence_bound_not_positive` 4 · `promotion_unreachable_from_baseline` 4 · `task_coverage_incomplete` 1 (an attempt can carry several) |

The SIL numbers are the point of the store: 42 mutation attempts produced one
KEEP and zero core promotions, with every rejection reason machine-recorded.
The loop's value here is the verifier discipline: noisy or immaterial
improvements do not survive the gates.

## MCPMark run index

Pass counts are per result directory, counted from `meta.json`
(`execution_result.success`). Directories overlap: retry and remainder runs
re-attempt tasks from earlier directories, so the per-service scores in the
GEODE docs deduplicate across directories (filesystem 25/30, postgres 20/21,
github 19/23 as of 2026-07-04).

| Result directory | Service | Passed/Tasks | Note |
|---|---|---:|---|
| `...20260704-mcpmark-verified-filesystem` | filesystem | 0/1 | first attempt, superseded by r2 |
| `...20260704-mcpmark-verified-filesystem-r2` | filesystem | 17/18 | |
| `...20260704-mcpmark-verified-filesystem-remainder` | filesystem | 8/11 | |
| `...20260704-mcpmark-verified-postgres` | postgres | 20/21 | |
| `...20260704-mcpmark-verified-github` | github | 6/12 | the 6 fails are `State Duplication Error` (unset `GITHUB_EVAL_ORG`): infra, not agent |
| `...20260704-mcpmark-verified-github-retry` | github | 13/17 | rerun with the eval org set |
| `...20260704-mcpmark-smoke-*` (filesystem/github/postgres, 7 dirs) | mixed | 3 passes | single-task easy smokes; several 0/1 while adapter argument normalization landed |
| `...20260704-mcpmark-smoke-notion*` (9 dirs) | notion | 0 | Stage-1 state-duplication stalls (expired browser session); mostly empty dirs kept for the audit trail |
| `...20260710-notion-smoke-unblock-r2` | notion | 1/1 | session re-login fix validated end to end |
| `...v1011-686ff372-20260731-mcpmark-filesystem-easy` | filesystem | 10/10 | released v1.0.11 regression batch |
| `...20260710-notion-smoke-unblock`, `...20260710-agentworld-cycle` | n/a | 0/0 | aborted starts (pre-relogin stall; 429 quota with the contaminated task removed per policy) |

## How to read a run

**MCPMark**, per task directory
(`<exp>/<model>__<service>/run-<k>/<task>/`):

- `meta.json` holds the scorecard: `execution_result.success` (verifier verdict),
  `error_message` (empty for agent-level fails, populated for infra fails;
  those are excluded from published scores and rerun),
  `agent_execution_time` / `task_execution_time`, `turn_count` (GEODE rounds),
  `token_usage` (input/output/cache-read; `cost_usd` is a LiteLLM-style
  estimate, not subscription billing), `reasoning_effort`, `mcp`.
- `messages.json` is not a full transcript. In this public snapshot, 78 files
  contain the serialized final-answer string and 11 aborted/no-output artifacts
  contain an empty list.
- `execution.log` exists for 78 task artifacts and holds the ordered MCP
  action/result trace (1,202 records in aggregate). Join it with `meta.json` to
  analyze tool behavior and verifier outcome; hidden model turns cannot be
  reconstructed from the public files.
- `run-<k>/summary.json` is the per-run aggregate the pipeline prints at the
  end.
- `mcpmark/logs*/` holds pipeline stdout including Stage 1 (state duplication),
  Stage 3 (verification output), Stage 4 (cleanup); the place to diagnose
  infra failures that never reach `meta.json`.

**tau2**, per simulation (`tau2/simulations/<run id>/`): tau2's native
simulation JSON: task, full agent/user turn log, reward, and termination
reason as emitted by the upstream harness. Run ids encode both model routes
(agent and user simulator), so subscription-only runs are separable from
comparator runs by name alone.

**Crucible**, per campaign (`crucible/runs/campaigns/<campaign>/state/`):
`attempts/<seq>-<hash>/` holds one mutation attempt: its candidate,
`evaluation-<id>/` result payloads, and the gate outcome recorded in the
attempt state. `crucible/gate-provenance/` holds the cross-campaign provenance:
`crucible_failure_manifest.json` (the frozen 114-row telecom failure set),
`crucible_gate_calibration.json` (where the `cheaploop_v1` budget numbers come
from), the G1 trace-replay report, and the G2/G3a task sets. Hardened campaigns
also carry identifier-free `prepare/power.json` and `prepare/runtime.json`
admission reports. When judgment is reached, `verdict.json` is the canonical
machine-readable outcome.

## Provenance contract

- Model route for GEODE runs: as named in each run id, provider
  `openai-codex`, source `subscription` unless the id says PAYG.
- Run interpretation lives in the GEODE repo, not here:
  `docs/eval/frontier-agentic-tool-use-benchmark-cases.md` (evidence ledger),
  `docs/eval/mcpmark-agentworld-comparison-runbook.md` (Agent-World comparison
  protocol), and the published run-record pages under
  `/docs/benchmarks/` on the docs site.
- Directories are append-only snapshots of local
  `artifacts/eval/harnesses/**` and `artifacts/eval/runs/crucible/**`
  (mapped to `crucible/runs/**`; the gate provenance files are generated
  into the GEODE repo's transient `tmp/crucible_*.json` and published here
  under the durable name `crucible/gate-provenance/`) at publish time. Nothing is rewritten after
  upload; corrections happen as new run directories.
- Rate-limit (429) failures are never counted as task failures: the affected
  task directory is deleted and the task rerun, because the harness resume
  logic would otherwise pin the failure permanently.

## What is excluded

- Upstream tau2-bench reference results (`data/tau2/results/final`, 576M):
  shipped by the benchmark authors, not GEODE output.
- Retired runtime checkpoint databases: opaque checkpoint/write payloads are not
  benchmark results, can contain full model and tool state, and have no public
  redaction contract. Only sanitized retirement receipts are retained under
  `reports/checkpoint-retirement/`.
- Inside the Crucible campaign store, `evaluator-tmp/` (baseline repo
  checkouts, ~630M) and `evaluator-home/` (uv package caches, ~3.3G) are
  excluded: they are byte-reproducible from the pinned commits and package
  versions recorded in the run state. The r1-r28 scoring series retains its
  evaluation outputs; the invalid r29-r35 operations-hardening series uses a
  narrower public receipt set and omits evaluator scratch and transcripts.
  The final verdict is retained whenever one was produced.
- Unopened sealed packs, selection manifests, salts, and attested row lists
  remain private. Identifier-free power/runtime reports may be published.
- Secrets: all files were scanned before upload for token/credential patterns
  (GitHub PAT, Notion keys, OpenAI keys, DB URIs, auth headers) and credential
  file names. Environment files (`.mcp_env`, `notion_state.json`) are never
  included.

## Reproduction

From an `eval-sys/mcpmark@cd45b7f` checkout with the GEODE repo installed
editable in its venv:

```bash
set -a; source .mcp_env; set +a
OPENAI_API_KEY=dummy \
.venv/bin/python -m plugins.benchmark_harness.run_mcpmark \
  --mcp <service> --task-suite <easy|standard> \
  --models geode-gpt-5.5 --agent geode --reasoning-effort xhigh \
  --k 1 --timeout 1200 \
  --exp-name <run-id> --output-dir ./results-geode-agentworld
```

`OPENAI_API_KEY=dummy` only satisfies the pipeline's env check; model calls go
through GEODE's `openai-codex` subscription provider. tau2 runs use the GEODE
tau2 adapter in the GEODE repo (`plugins/benchmark_harness/tau2_geode_agent.py`).
Exact per-run commands and environment state are recorded in the GEODE repo's
`docs/eval/mcpmark-agentworld-comparison-runbook.md`.
