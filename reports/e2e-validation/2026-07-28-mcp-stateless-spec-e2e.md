# MCP 2026-07-28 stateless-spec response — live E2E validation

Validation of the GEODE v1.0.2 landing (ADR-014 in the main repo): MCP SDK
pinned to the v1 line (`mcp>=1.28,<2`), and the hand-rolled stdio client now
declares protocol revision `2025-06-18`, records the server-negotiated
revision, and fail-loud-rejects revisions outside its supported classic set.

- Captured (UTC): 2026-07-28T19:57:52Z · session `e2e-mcp-20260729` (KST day)
- GEODE revision: `dd53971f0` (v1.0.2, main) · MCP python-sdk 1.29.0
- Probe: in-process `AgenticLoop` + `MCPServerManager` limited to the
  `geode-mcp` stdio server; LLM on the ChatGPT-subscription backend
  (`gpt-5.5`, adapter `codex-oauth`, `source=subscription`,
  endpoint `chatgpt.com/backend-api/codex`, all calls HTTP 200)

## Phase A — wire level (no LLM)

| Case | Result |
|---|---|
| `StdioMCPClient` → `geode-mcp` loopback | connect=True, negotiated `protocolVersion` = `2025-06-18`, recorded in `server_protocol_version` |
| Tool surface | 6 tools: `get_health`, `query_memory`, `run_agent`, `self_improving_apply`, `self_improving_propose`, `self_improving_status` |
| `get_health` call | `{"version": "1.0.2", "model": "gpt-5.6-sol", "ensemble_mode": "single", "anthropic_configured": true, "openai_configured": true, "anthropic_credential_source": "auto", "openai_credential_source": "auto"}` |
| Fake stateless-only server answering `"2026-07-28"` to `initialize` (real subprocess) | rejected: connect=False, `server_protocol_version=None`, child terminated (fail-loud path) |

## Phase B — agent level (subscription LLM)

Prompt (EN): call `get_health`, report status in one sentence; then call
`query_memory("MCP")` and state how many entries returned. Tool surface
restricted to those two MCP tools.

| Observable | Value |
|---|---|
| Termination | natural, rounds 3/6, tool calls 2 |
| MCP dispatch | `get_health → geode`, `query_memory → geode` (raw tool names; client-path MCP tools carry no `mcp__` prefix) |
| LLM calls | 2 · in 4,794 / out 89, then in 9,638 / out 290 (cache read 4,608) |
| Displayed cost | $0.0266 + $0.0362 (accounting display; subscription-billed, no marginal spend) |
| Final answer | correct on both sub-tasks (runtime v1.0.2 healthy; 1 memory context entry) |

Side observation (pre-existing, unrelated to the MCP change): the loop's
reflection subsystem got no `record_reflection` tool_use block from the codex
backend in 3/3 reflection calls and fell back to previous state (warning only,
non-fatal).

## Trajectory release

Normalized per `TRAJECTORIES.md` (`geode.trajectory@2026-07-29` envelope,
dialogue + tool classes, strict-adjacency call/result pairing, lossy tool
payloads declared):

- `trajectories/geode-agenticloop-mcp-2026-07-28-spec-e2e-20260728T202349Z-7acb62a4184c/`
- `trajectory.json` sha256 `8b77e3b05eeba51374cef5b640ddf1109c323f4e3defe869934bbadd43138b42` (9 events)
- manifest sha256 `7acb62a4184c8e2521693949adeaa73ba7321725d56a1b93220285a87f3991f4`
