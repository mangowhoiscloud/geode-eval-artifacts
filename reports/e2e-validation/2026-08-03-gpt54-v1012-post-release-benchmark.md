# GEODE v1.0.12 GPT-5.4 post-release regression — 2026-08-03

## Outcome

| Benchmark | Result | Terminal evidence | Reading |
|---|---:|---|---|
| MCPMark filesystem/easy | **9/10 (90.0%)** | 9 verifier passes, 1 verifier failure | The released runtime, subscription route, MCP transport, and verifier path completed all ten tasks. `file_context__uppercase` created all five files but left `file_01.txt` partly non-uppercase. |
| Tau2 `mock/create_task_1` | **0/1** | `USER_STOP`, 13.75s | The user simulator stopped before a verifier-compatible state change. Communication scored 1.0, but DB and required action scored 0.0. |
| Tau2 Telecom-small roaming task | **0/1** | `MAX_STEPS`, 236.73s | Fourteen paired tool calls repeated lookup and network diagnostics; the simulation exhausted 50 steps before native DB/action evaluation. |

All three failures are retained as behavior evidence. None was retried or
reclassified as infrastructure contamination. There was no authentication,
quota, provider-adapter, MCP transport, or harness exception.

The Tau2 pair is a release smoke, not a second full cycle. The authoritative
three-domain GPT-5.4 diagnostic remains the 278-task run at the same runtime
code: **Airline 42/50, Retail 79/114, Telecom 79/114, total 200/278 =
0.7194**. Its `geode_user` route, unfrozen contract, and retry-lineage limits
remain disclosed in the
[full-cycle record](2026-08-03-gpt54-tau2-full-cycle.md).

## Provenance

| Field | Value |
|---|---|
| GEODE release | `v1.0.12`, commit `f99cea63dd39eb3f49fb00ac36e2e2804518c100`, tree `1349ae7886b35110016a469a0b0d0b6b9a9fc6d6` |
| Distribution | GitHub Release and public PyPI `geode-agent==1.0.12` independently verified before measurement |
| Model route | `gpt-5.4`, OpenAI subscription, effort `high`; Tau2 used the same route for `geode_agent` and `geode_user` |
| MCPMark | `eval-sys/mcpmark@cd45b7f57923b9b3985467f5139927575f83141c`, filesystem/easy, 10 tasks, k=1, 1,200s task timeout |
| Tau2 | `sierra-research/tau2-bench@1901a301961cbbe3fd11f3e84a2a376530c759e3`; mock max steps 8, Telecom max steps 50, no task retry |

MCPMark ran against the exact released GEODE tree through its native adapter.
Tau2 used the same release tree and saved native `results.json` plus GEODE
trajectory snapshots. Subscription decoding parameters other than effort are
not a controlled research baseline, so the MCPMark change from v1.0.11
GPT-5.6 **10/10** to v1.0.12 GPT-5.4 **9/10** is model-confounded and is not
attributed to the release alone.

## Measurements

MCPMark completed in 802.18 seconds with 53 turns, 302,984 input tokens, and
30,238 output tokens. Its aggregate `total_tokens` and
`total_reasoning_tokens` remain zero despite populated input/output fields and
are not treated as measurements. The sole failure's upstream verifier confirms
that the output directory and all five files existed, while `file_01.txt`
failed the uppercase content check.

The Tau2 mock episode records reward 0.0, DB reward 0.0, action reward 0.0,
and communicate reward 1.0. The Telecom episode records no component score
because `MAX_STEPS` is a premature terminal state. Its fourteen tool pairs are
four `get_details_by_id`, three `check_network_status`, two
`get_customer_by_phone`, two `get_data_usage`, and one each of
`toggle_roaming`, `check_data_restriction_status`, and `check_vpn_status`.
The repeated diagnostics are behavior, not a storage or correlation defect.

## Record and storage quality

| Scope | Stable trajectories | Canonical events | Tool pairs | Scope complete | Replay complete |
|---|---:|---:|---:|---:|---:|
| MCPMark | 10 | 182 | 56/56 | 10/10 | 0/10 |
| Tau2 smoke pair | 2 | 234 | 16/16 | 2/2 | 0/2 |

Every event identifier is unique, ordinals are contiguous, and no call or
result is orphaned. `scope_complete` means every selected task is represented;
it does not imply byte replay. Provider-private state, hidden reasoning,
private prompts, full external sandbox state, SQLite/WAL, mutable checkpoints,
usage ledgers, and raw runtime JSONL are excluded, so every release correctly
declares `replay_complete=false`.

The source authorities stay separate:

- MCPMark `meta.json`, `messages.json`, ordered `execution.log`, and
  `summary.json` own task execution and verifier results.
- Tau2 `results.json` owns score and termination; GEODE snapshots own measured
  extraction provenance, while runtime `sessions.db:session_events` remains
  the canonical local behavior history.
- `geode.trajectory@1` is the immutable correlation and behavior projection
  for external loops. It does not replace native SIL or Crucible evidence.

This makes the package safe for `PostVerify`, SIL, or Crucible consumption:
an outer loop can join model behavior to an executable verifier result without
mistaking `Stop`, `USER_STOP`, or a complete trace for task success.

## Privacy and integrity

The release verifier recomputed both manifest anchors, all trajectory hashes,
event order, identifiers, pairings, source-digest joins, privacy attestations,
and secret scans. An independent native-receipt audit then checked all 35
raw/public file size and SHA-256 pairs against the restricted local source,
parsed 42 JSON documents, and scanned 52 staged files. It found zero local
home paths, emails, E.164 or dashed phone numbers, OpenAI keys, GitHub tokens,
bearer-token values, or AWS access keys.

MCPMark's public copy masks local home paths in 16 of 31 native files. Tau2's
public Telecom receipt masks 14 phone and 2 email occurrences; both snapshots
mask eight local paths. Raw-source and public-copy digests remain separate in
each `publication.json` so the privacy projection cannot be mistaken for the
native bytes.

## Public anchors

- MCPMark native receipts:
  `mcpmark/results-geode-agentworld/geode-gpt54-high-v1.0.12-f99cea63-20260803-mcpmark-filesystem-easy/`
- Tau2 native receipts:
  `tau2/simulations/geode-gpt54-high-v1.0.12-f99cea63-geode-user-{mock-smoke,telecom-small-01}-20260803/`
- MCPMark trajectory release:
  `trajectories/mcpmark-geode-gpt54-v1.0.12-f99cea63-filesystem-easy-20260803T104819Z-9636b39c16fb/`
- MCPMark manifest SHA-256:
  `9636b39c16fb494b5c7e97b8052451e521055ef08e17fddeb5a129b9e367d267`
- Tau2 trajectory release:
  `trajectories/tau2-geode-gpt54-v1.0.12-f99cea63-geode-user-mock-telecom-small-20260803T104819Z-fd524ce7a3cb/`
- Tau2 manifest SHA-256:
  `fd524ce7a3cb1f1088f0e7a1531130d6302fb9f43d57a734303071bf6fd72288`

Remote readback remains required until the artifact PR is merged.
