# GPT-5.4 subscription tau2 full-cycle record — 2026-08-02 KST

## Outcome

| Scope | Reward / pass^1 | Duration | Termination | Behavioral reading |
|---|---:|---:|---|---|
| `mock/create_task_1` | **0.0 / 0.000** | 25.326s | `user_stop` | The agent made the useful `get_users` read, then supplied optional `description=""` to `create_task`; tau2's exact action and DB comparators rejected the extra argument. |
| Telecom `small`, fixed first task | **1.0 / 1.000** | 119.831s | `user_stop` | Customer and line diagnostics completed, the simulated user enabled device roaming, and DB state, mobile-data status, excellent-speed, and `toggle_roaming` checks all passed. |

Both runs completed without provider, quota, adapter, agent, or user errors.
The mock failure is retained as behavior evidence; it was not retried, deleted,
or relabeled. The two-row scope is a GEODE route regression matching the latest
GPT-5.6 release cycle, not a native-user leaderboard claim or a full-domain
tau2 score.

## Provenance

| Field | Value |
|---|---|
| GEODE measured revision | `afaab52ba2fc0ee8b0ffcdf251371e65be6f0933`, tree `585bdaa22dd87403cdb5676cf840371778a14460` |
| Runtime surface | unreleased GEODE feature worktree (`1.0.11+unreleased`) |
| Agent and user route | `gpt-5.4`, provider `openai`, source `subscription`, effort `high` |
| Credential proof | Codex OAuth present; GEODE source inference resolved `openai -> subscription` |
| tau2 harness | `sierra-research/tau2-bench@1901a301961cbbe3fd11f3e84a2a376530c759e3`, `tau2==1.0.0` |
| Task pack | `mock/create_task_1`; Telecom split `small`, task `[mobile_data_issue]user_abroad_roaming_enabled_off[PERSONA:None]` |
| Sampling | one trial per task, concurrency 1, seed 300; max steps 8 / 50 |
| Upstream license | tau2-bench MIT |

The live runs occurred before the later picker-only directional migration fix;
that fix cannot affect the explicit model/provider/source arguments or the
recorded agent behavior. The run identifiers therefore retain the exact
measured revision prefix `afaab52b`.

## Native verifier detail

The mock action expected only `user_id=user_1` and
`title="Important Meeting"`. GPT-5.4 called `get_users`, then emitted
`create_task(user_id="user_1", title="Important Meeting", description="")`.
The write executed, but the exact action comparator and final DB comparator
both scored zero.

The Telecom episode contains eight exactly paired tools:

- assistant reads: `get_customer_by_phone`, two `get_details_by_id` calls, and
  `get_data_usage`;
- user actions: two `check_network_status` calls, `toggle_roaming`, and
  `run_speed_test`.

The official verifier records DB match 1.0, `toggle_roaming` 1.0,
`assert_mobile_data_status` 1.0, and `assert_internet_speed` 1.0.

## Trajectory and storage quality

| Scope | Canonical events | Exact tool pairs | Missing IDs / orphan pairs | Scope complete | Replay complete |
|---|---:|---:|---:|---:|---:|
| mock | 31 | 2/2 | 0 / 0 | yes | no |
| Telecom | 127 | 8/8 | 0 / 0 | yes | no |

The `geode.trajectory@1` sidecars were projected from
`sessions.db:session_events`; all 158 event IDs have contiguous ordinals and
stable session/turn correlation. Replay completeness is intentionally false:
dialogue and tool bodies are represented by digests, while runtime SQLite,
JSONL, provider-private state, hidden reasoning, credentials, and private
prompts are excluded.

Tau2 `results.json` remains score authority. The accompanying
`crucible_tau2_trajectory_snapshot.v3` records are diagnostic, with
`candidate_surface=unfrozen_git` and `promotion_authority=none`. The runner's
standalone default wrote `stage=train`; that source label is retained rather
than silently rewritten, but it confers no train-set or promotion authority.
The task IDs and this report define the actual benchmark scope.

## Privacy and digest boundary

The restricted raw native receipt SHA-256 values are:

- mock: `f576aa91e5631f2fd85e33a8a4867becda91af45f12befa81eefe86f03742615`;
- Telecom: `75264b7c86d44f958061ee7f1939153ed9d135e4355eca9b54c0380cb152309a`.

The mock public copy is byte-identical to its raw receipt. The Telecom public
copy replaces the synthetic target phone and email and therefore has digest
`d2d8e1ca9296e7f044a2be5062f1c14c8427107bf5a66c74929a2d878538297f`.
Local absolute paths are masked in public snapshots. The four-file public
native-receipt map has canonical digest
`117a1f7f6e88bcdc792c0c17a58c5aff96c7df1ffa0e2aa216bbd565871b9a39`.

The release scan found zero absolute-home, email, OpenAI-key, GitHub-token,
bearer-token, AWS-key, query-secret, or known-secret matches. The content-bound
privacy attestation digest is
`9fcb3ccfb07c9a376d4d3152af3e92603fd11ebf01149914ce1512408e02e7fa`.

## External-loop compatibility

- SIL keeps Inspect `.eval`, executable verifier outputs, and mutation and
  attribution ledgers authoritative. The portable trajectory is a correlation
  sidecar, not an evaluator replacement.
- Crucible requires a frozen experiment contract and explicit arm for promotion
  evidence. These standalone runs have neither and correctly retain
  `promotion_authority=none`.
- Remote consumers can join the native tau2 receipt to the normalized behavior
  view by raw digest without importing GEODE's SQLite/WAL or mutable JSONL.

## Public anchors

- Native receipts: `tau2/simulations/geode-gpt54-high-afaab52b-geode-user-*/`
- Stable release: `trajectories/tau2-geode-gpt54-afaab52b-mock-telecom-small-20260801T173245Z-2dc79cb569f0/`
- Manifest SHA-256: `2dc79cb569f03e5f44ce008b32fd8af86f8388ab04341ee8f91c74fdffb6aa6b`
- Privacy review: `reports/privacy-reviews/2026-08-02-geode-gpt54-tau2.json`

Remote readback remains required until this artifact PR is merged.
