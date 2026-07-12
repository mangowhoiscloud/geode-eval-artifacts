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

## Provenance contract

- Model route for GEODE runs: `gpt-5.5` (or as named in each run id), provider
  `openai-codex`, source `subscription`, reasoning effort in the run id
  (`xhigh`/`high`). PAYG comparator runs are named accordingly.
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
  (GitHub PAT, Notion keys, OpenAI keys, DB URIs, auth headers). Environment
  files (`.mcp_env`, `notion_state.json`) are never included.

## Reproduction

Each MCPMark run directory name encodes `<agent>-<model>-<effort>-<date>-<suite>`;
the exact launch command is recorded in the GEODE repo runbook. The launcher is
`plugins/benchmark_harness/run_mcpmark.py` in the GEODE repository (registers
the GEODE agent against upstream MCPMark without patching it).
