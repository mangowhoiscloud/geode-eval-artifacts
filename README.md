# GEODE Evaluation Artifacts

Raw run logs behind the benchmark numbers published in the
[GEODE docs](https://mangowhoiscloud.github.io/geode/docs/benchmarks/results).
Every score GEODE publishes cites a result directory; this repository is where
those directories live, unmodified, so any reported number can be traced back
to the verifier output and full message transcript that produced it.

## Layout

| Path | Content | Producing harness |
|---|---|---|
| `mcpmark/results-geode-agentworld/` | MCPMark run directories. Per task: `meta.json` (route, timing, tokens, verifier result), `messages.json` (full agent transcript), `summary.json` per run | `eval-sys/mcpmark@cd45b7f` + GEODE `BaseMCPAgent` adapter |
| `mcpmark/logs/`, `mcpmark/logs-cycle/` | Pipeline stdout logs (state duplication, verification, cleanup stages) | same |
| `tau2/simulations/` | tau2-bench simulation JSONs for GEODE-owned runs (`geode-*`, `crucible-*`, smoke variants) | `sierra-research/tau2-bench@1901a30` (`tau2==1.0.0`) + GEODE participant adapter |
| `crucible/runs/campaigns/` | Crucible (self-improving-loop measurement) campaign run state: per-attempt state, evaluations, gate outcomes | GEODE Crucible harness over tau2-bench |
| `crucible/runs/{row-cache,trajectory-snapshots}/` | Row cache and trajectory snapshots backing the campaign store (the local `gates/` store is currently empty; gate outcomes live inside each campaign's attempt state) | same |
| `crucible/tmp/` | Gate provenance artifacts from the repo `tmp/`: failure manifest, `cheaploop_v1` gate calibration, G1 trace-replay, G2/G3a task sets | same |

## What was used

Everything below is also recorded per run inside the artifacts themselves;
this table is the summary of the stack that produced them.

| Component | Value |
|---|---|
| MCPMark harness | `eval-sys/mcpmark@cd45b7f` (MCPMark Verified release; standard = 127 pinned tasks), local Python 3.12 venv, official `pipeline.py` unpatched |
| GEODE entry point | `plugins/benchmark_harness/run_mcpmark.py` in the GEODE repo — registers the `geode` agent (a `BaseMCPAgent` wrapping GEODE's `AgenticLoop`) before `pipeline.main()` |
| MCP servers (MCPMark) | GitHub: `ghcr.io/github/github-mcp-server:v0.15.0` (Docker stdio) · Postgres: `postgres-mcp==0.3.0` via pipx · Playwright: `@playwright/mcp@0.0.68` (headless chromium) · Notion: `@notionhq/notion-mcp-server` (stdio) · Filesystem: upstream MCPMark default |
| tau2 harness | `sierra-research/tau2-bench@1901a30` (`tau2==1.0.0`), GEODE agent + GEODE user-simulator adapters; native `user_simulator` comparator runs labeled separately |
| Model routes | Primary: `gpt-5.5`, provider `openai-codex`, source `subscription` (effort in run id: `xhigh`/`high`). Comparators: `gpt-5.2` (subscription and PAYG, labeled in run id). Crucible train campaigns of 2026-07-11/12: `gpt-5.4`. Decoding parameters are not controllable on the subscription route — treat cross-paper comparisons as directional |
| Verifiers | Upstream per-task verify scripts (MCPMark) and tau2 reward/DB-state checks — never GEODE-authored judges |

## Run naming

- MCPMark: `geode-<model><effort>-<date>-<purpose>[-<slice>]`, e.g.
  `geode-gpt55-xhigh-20260704-mcpmark-verified-postgres`. `smoke-*` = single
  tasks from the `easy` suite; `verified-*` = the standard (Verified) suite;
  `notion-smoke-unblock*` = the 2026-07-10 session-expiry fix validation.
- tau2 simulations:
  `crucible-tau2-<gate>-<domain>-<candidate>-<agent route>-<user route>-n{N}k{K}[-suffix]`
  for Crucible probes (gate ∈ readiness/cheaploop/g2/g3a/g4), and
  `geode-<model>-<domain>-<scope>-<date>` for native GEODE runs.
- Crucible campaigns: `tau2-telecom-gpt54-train-<date>-r<N>` (r1–r28,
  2026-07-11/12) plus `crucible-rowcache-live-*` cache-priming runs.

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
| `...20260704-mcpmark-verified-github` | github | 6/12 | the 6 fails are `State Duplication Error` (unset `GITHUB_EVAL_ORG`) — infra, not agent |
| `...20260704-mcpmark-verified-github-retry` | github | 13/17 | rerun with the eval org set |
| `...20260704-mcpmark-smoke-*` (filesystem/github/postgres, 7 dirs) | mixed | 3 passes | single-task easy smokes; several 0/1 while adapter argument normalization landed |
| `...20260704-mcpmark-smoke-notion*` (9 dirs) | notion | 0 | Stage-1 state-duplication stalls (expired browser session); mostly empty dirs kept for the audit trail |
| `...20260710-notion-smoke-unblock-r2` | notion | 1/1 | session re-login fix validated end to end |
| `...20260710-notion-smoke-unblock`, `...20260710-agentworld-cycle` | — | 0/0 | aborted starts (pre-relogin stall; 429 quota with the contaminated task removed per policy) |

## How to read a run

**MCPMark**, per task directory
(`<exp>/<model>__<service>/run-<k>/<task>/`):

- `meta.json` — the scorecard: `execution_result.success` (verifier verdict),
  `error_message` (empty for agent-level fails, populated for infra fails —
  infra fails are excluded from published scores and rerun),
  `agent_execution_time` / `task_execution_time`, `turn_count` (GEODE rounds),
  `token_usage` (input/output/cache-read; `cost_usd` is a LiteLLM-style
  estimate, not subscription billing), `reasoning_effort`, `mcp`.
- `messages.json` — the full transcript: every model turn and MCP tool
  call/result the agent saw. This is the file to audit *why* a task passed or
  failed.
- `run-<k>/summary.json` — the per-run aggregate the pipeline prints at the
  end.
- `mcpmark/logs*/` — pipeline stdout including Stage 1 (state duplication),
  Stage 3 (verification output), Stage 4 (cleanup); the place to diagnose
  infra failures that never reach `meta.json`.

**tau2**, per simulation (`tau2/simulations/<run id>/`): tau2's native
simulation JSON — task, full agent/user turn log, reward, and termination
reason as emitted by the upstream harness. Run ids encode both model routes
(agent and user simulator), so subscription-only runs are separable from
comparator runs by name alone.

**Crucible**, per campaign (`crucible/runs/campaigns/<campaign>/state/`):
`attempts/<seq>-<hash>/` holds one mutation attempt — its candidate,
`evaluation-<id>/` result payloads, and the gate outcome recorded in the
attempt state. `crucible/tmp/` holds the cross-campaign provenance:
`crucible_failure_manifest.json` (the frozen 114-row telecom failure set),
`crucible_gate_calibration.json` (where the `cheaploop_v1` budget numbers come
from), the G1 trace-replay report, and the G2/G3a task sets.

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
  (mapped to `crucible/runs/**`; repo-root `tmp/crucible_*.json` maps to
  `crucible/tmp/`) at publish time. Nothing is rewritten after
  upload; corrections happen as new run directories.
- Rate-limit (429) failures are never counted as task failures: the affected
  task directory is deleted and the task rerun, because the harness resume
  logic would otherwise pin the failure permanently.

## What is excluded

- Upstream tau2-bench reference results (`data/tau2/results/final`, 576M):
  shipped by the benchmark authors, not GEODE output.
- Inside the Crucible campaign store, `evaluator-tmp/` (baseline repo
  checkouts, ~630M) and `evaluator-home/` (uv package caches, ~3.3G) are
  excluded: they are byte-reproducible from the pinned commits and package
  versions recorded in the run state, and contain no evaluation output. All
  actual run data (attempts, evaluations, gate outcomes, trajectories) is
  included.
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
