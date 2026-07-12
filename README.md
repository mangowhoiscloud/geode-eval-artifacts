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
  `artifacts/eval/harnesses/**` at publish time. Nothing is rewritten after
  upload; corrections happen as new run directories.

## What is excluded

- Upstream tau2-bench reference results (`data/tau2/results/final`, 576M):
  shipped by the benchmark authors, not GEODE output.
- Crucible internal SIL run store (`artifacts/eval/runs/crucible`, ~4GB):
  internal self-improving-loop experiment logs, out of scope for benchmark
  evidence. Available on request as a release tarball.
- Secrets: all files were scanned before upload for token/credential patterns
  (GitHub PAT, Notion keys, OpenAI keys, DB URIs, auth headers). Environment
  files (`.mcp_env`, `notion_state.json`) are never included.

## Reproduction

Each MCPMark run directory name encodes `<agent>-<model>-<effort>-<date>-<suite>`;
the exact launch command is recorded in the GEODE repo runbook. The launcher is
`plugins/benchmark_harness/run_mcpmark.py` in the GEODE repository (registers
the GEODE agent against upstream MCPMark without patching it).
