# GPT-6 Astra subscription E2E smoke

This append-only bundle records one preregistered GEODE end-to-end smoke on
Terminal-Bench 2.1. GEODE reached `gpt-6-astra` with `high` reasoning through
the current OpenAI subscription route, completed the canonical
`openssl-selfsigned-cert` container task, and received verifier reward **1/1**.

## Result

| Field | Observed value |
|---|---|
| GEODE | 1.0.27 at `132dc61f90b0fe097cf16b01efa564e88d9d8dc9` |
| Model route | `gpt-6-astra` / `high` / OpenAI subscription |
| Harness | Harbor 0.22.0 |
| Dataset | `terminal-bench/terminal-bench-2-1@6` |
| Task | `terminal-bench/openssl-selfsigned-cert` |
| Canonical verifier | 1/1 reward; 6/6 verifier checks passed |
| Runtime | 3 rounds; 2 paired terminal tool calls; natural termination |
| Tokens | 10,442 input; 1,948 output; 0 cached |
| Retry or fallback | none |

The Harbor `cost_usd` value of `$0.20182` is a price-table estimate, not an
OpenAI subscription billing receipt.

## Evidence map

| Question | Evidence |
|---|---|
| What was frozen before execution? | [`run-spec.json`](run-spec.json) |
| Was there a retry or fallback? | [`attempts.jsonl`](attempts.jsonl) |
| What result is supported? | [`analysis.json`](analysis.json) |
| What did Harbor aggregate? | [`result.json`](raw/harbor/terminalbench21-astra-high-openssl-smoke-20260904t202725z/result.json) |
| Which canonical checks passed? | [`ctrf.json`](raw/harbor/terminalbench21-astra-high-openssl-smoke-20260904t202725z/openssl-selfsigned-cert__nCXHtTa/verifier/ctrf.json) and [`reward.txt`](raw/harbor/terminalbench21-astra-high-openssl-smoke-20260904t202725z/openssl-selfsigned-cert__nCXHtTa/verifier/reward.txt) |
| How did the runtime progress? | [reviewed trajectory release](trajectories/terminalbench-geode-terminalbench21-astra-high-openssl-smoke-20260904t202725z-20260904T204003Z-e248cf31969e/) |

## Claim boundary

This is a one-task, one-repetition account-scoped E2E smoke. It demonstrates
route access and successful execution for this scenario. It does **not**
estimate Terminal-Bench suite accuracy or variance, establish leaderboard
rank, compare GEODE with another harness, or prove general GPT-6 Astra
availability. The canonical linux/amd64 image ran under Docker Desktop on an
arm64 macOS host.

Raw model reasoning, OAuth material, prompts, tool payloads, ATIF, terminal
recordings, local paths, and unreviewed task outputs remain private. The public
GEODE trajectory is scope-complete and intentionally replay-incomplete: nine
payload bodies are represented only by digests.
