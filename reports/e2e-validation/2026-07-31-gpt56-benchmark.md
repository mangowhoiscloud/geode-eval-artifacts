# GPT-5.6 subscription benchmark record — 2026-07-31

## Provenance

| Field | Value |
|---|---|
| GEODE revision | `edb74602bb2e1e4d627cb6aa1f0b94072a57da62` |
| GEODE tree | `046f5a809ce9b370fef45810ca87d4c933a8ea1f` |
| Model route | `gpt-5.6-sol`, OpenAI subscription, effort `high` |
| MCPMark | `eval-sys/mcpmark@cd45b7f`, filesystem/easy, k=1 |
| tau2 | `sierra-research/tau2-bench@1901a30`, `tau2==1.0.0` |
| Upstream licenses | MCPMark Apache-2.0; tau2-bench MIT |

## MCPMark

- Official verifier: **9/10 (90.0%)**.
- Wall time: 799.435 s; 54 turns.
- Usage: 799,679 input, 10,976 output, 97,792 cache-read tokens.
- Recorded estimate: $3.887611; this is not subscription billing.
- Failure: `file_context__uppercase` created all five files but left
  `file_01.txt` not fully uppercased.
- One transient response-stream disconnect occurred after the first task had
  produced its files. That task passed every official integrity check; no 429
  occurred. The console-only disconnect is not present in the task receipt.
- Upstream `summary.json.token_usage.total_tokens` and
  `total_reasoning_tokens` are zero despite populated input/output fields, so
  those aggregate fields are not reported as measurements.

## tau2

| Scope | Result | Duration | Behavioral reading |
|---|---:|---:|---|
| `mock/create_task_1` | 0/1 | 14.58 s | Tool call executed, but the model added optional `description=""`; exact action and DB comparators rejected it. |
| Telecom small first task | 0/1 | 51.91 s | Account diagnostics were correct, then the agent transferred to a human instead of guiding the user-side roaming/device workflow. |

Both tau2 runs terminated normally with `USER_STOP`; neither contained a
provider, quota, or adapter exception. The first attempt before measurement
installed GEODE runtime dependencies into the pinned harness environment.
Two Telecom preflights produced no run artifact: `telecom_small`'s loader does
not accept the generic split argument, and the default `base` split excludes
the selected small task. The measured run used the official `small` split.

## Public artifacts

- MCPMark receipts: `mcpmark/results-geode-agentworld/geode-gpt56-sol-high-edb74602b-20260731-mcpmark-filesystem-easy/`
- tau2 receipts: `tau2/simulations/<run-id>/`
- MCPMark normalized trajectories: `trajectories/mcpmark-geode-gpt56-edb74602b-filesystem-easy-20260731T034305Z-b86f5071cbe0/`
- tau2 normalized trajectories: `trajectories/tau2-geode-gpt56-edb74602b-mock-telecom-small-20260731T034305Z-4ec1c13434d1/`

All published JSON/JSONL-equivalent records parse. Local absolute usernames and
synthetic telecom personal fields were redacted. Credential/token pattern scans
returned zero matches. Runtime homes, SQLite databases, hidden reasoning, and
general session stores were excluded.
