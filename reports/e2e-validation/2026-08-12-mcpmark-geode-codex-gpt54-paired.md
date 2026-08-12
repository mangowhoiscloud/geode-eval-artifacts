# GPT-5.4 GEODE × Codex MCPMark paired diagnostic — 2026-08-12

## Result

The same GPT-5.4 subscription model, `high` effort, ten
`filesystem/easy` tasks, upstream fixture reset, and task verifier produced
the same outcome for GEODE and Codex CLI: **9/10 (90.0%)** each.

This is a paired harness diagnostic, not an MCPMark Verified leaderboard
submission. The current MCPMark checkout was pinned to
`eval-sys/mcpmark@cd45b7f57923b9b3985467f5139927575f83141c`; each arm ran one
trial with a 1,200-second task timeout. GEODE's implementation is pinned by
feature commit `85967a498451f493055cb94738410378d6eddbe9` and PR
[`mangowhoiscloud/geode#2958`](https://github.com/mangowhoiscloud/geode/pull/2958).

| Metric | GEODE | Codex CLI |
|---|---:|---:|
| Passed / attempted | 9 / 10 | 9 / 10 |
| Agent time | 747.2s | 745.5s |
| MCP calls | 50 | 116 |
| Input tokens | 447,376 | 1,518,869 |
| Cached input tokens | 195,584 | 1,366,400 |
| Output tokens | 25,157 | 25,477 |
| Separately exposed reasoning tokens | n/a | 10,144 |

Native counters are retained as harness diagnostics and are not asserted to be
billing-equivalent across the two runtimes.

The sole failure was the same `file_context/uppercase` task. Both agents
uppercased all five requested files but added one trailing LF absent from each
source. The exact-string upstream verifier therefore failed both attempts.
No retry was used to erase the paired failure.

The largest efficiency divergence was Codex's
`folder_structure/structure_analysis`: 55 MCP calls, including 53
`list_directory` calls, versus GEODE's four calls using the available tree
operation. GEODE's slowest task was instead `file_context/file_splitting`.
Equal aggregate time therefore does not imply equal search behavior.

## Public trajectory releases

- GEODE:
  [`mcpmark-geode-gpt54-high-geode-codex-paired-filesystem-easy-20260812T060733Z-3ea7869be85a`](../../trajectories/mcpmark-geode-gpt54-high-geode-codex-paired-filesystem-easy-20260812T060733Z-3ea7869be85a/)
- Codex CLI:
  [`mcpmark-codex-gpt54-high-geode-codex-paired-filesystem-easy-20260812T060733Z-871a6c2ae92c`](../../trajectories/mcpmark-codex-gpt54-high-geode-codex-paired-filesystem-easy-20260812T060733Z-871a6c2ae92c/)

| Quality | GEODE | Codex CLI |
|---|---:|---:|
| Trajectories | 10 | 10 |
| Canonical events | 180 | 306 |
| Tool call/result pairs | 50/50 | 116/116 |
| Orphan calls/results | 0/0 | 0/0 |
| Scope-complete | 10/10 | 10/10 |
| Replay-complete | 0/10 | 0/10 |
| Source log digests verified | 10/10 | 10/10 |
| Public secret-scan findings | 0 | 0 |

Replay incompleteness is intentional. Prompt, reasoning, dialogue, tool, and
result bodies are represented only by SHA-256 digests. Raw Codex JSONL, GEODE
session events, stderr, runtime databases, credentials, local paths, and
mutable fixture state are excluded. Each manifest records the reviewed
allowlist, exact source-digest checks, and reduced replay fidelity.

## Claim boundary

This run supports one direct claim: under this frozen ten-task easy profile,
GEODE and Codex had identical pass/fail outcomes. It does not establish general
runtime parity, a statistically resolved efficiency ranking, or a current
MCPMark Verified score. Repetition was not spent because the paired score
difference was exactly zero.
