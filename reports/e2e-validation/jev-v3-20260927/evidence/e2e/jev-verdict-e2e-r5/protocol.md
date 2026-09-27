# Budget recovery epoch

Root540/6rounds, Harbor570, watchdog1290. See R/05-budget-amendment-20260927.md; old180 results preserved. Source pin and task runtime copies remain pending until the new commit is verified.

# Jev v3 paired-slot E2E: private runner protocol

Status: preparation code. No freeze, execution, publication or adoption is authorized by this file. Each `--reviewed` mode needs its own approval: infrastructure, freeze and live execution. The design authority is 05 v2 (§2.4-§2.6, §3, §4.3, §7, §9); this file only records how the runner implements it.

## Units

| Unit | Kind | Judge primitive | Slots x arms | Primary | Needs |
| --- | --- | --- | --- | --- | --- |
| U0d | admission | Choice | 2 x A/B | `verdict_e2e_admission_success` /4 | none |
| U0e | admission | Noul | 1 x A/B | `noul_e2e_admission_success` /2 | none |
| U0f | admission | Choice | 2 x C | `cascade_e2e_admission_success` /2 | U0d; only with arm C |
| U7r0 | natural | Choice | 12 x A/B(/C) | `m8n_strict_success_delta` /12 | U0d (+U0f with C) |
| U7r1 | natural | Choice | 12 x A/B(/C) | `m8n_strict_success_delta` /12 | U0d, U7r0 (+U0f with C) |
| U8c | injected | Choice | 18 x A/B | `m8i_choice_recovery_delta` /18 | U0d |
| U8n | injected | Noul | 18 x A/B | `m8i_noul_recovery_delta` /18 | U0e |

Arm A is the Astra xhigh final judge (`llm`), arm B is direct Jev 1.13.0 (`jev`), and arm C is the cascade (`cascade`). Arm C stays off unless `--arm-c` is given together with the selection freeze that fixes tau. It is pre-registered for U0f and U7 only. Root, repair and reflection calls are GPT-6 Astra xhigh on the Codex subscription in every arm. Models, effort, repetitions and scale come from the design. The runner has no option to change them.

## Slots

- The slot matrix is `e2e-slots.jsonl`, copied from run-packets and bound by the payload manifest and freeze. U7 with C uses `launch_order_if_c`. Rows marked `conditional_on_arm_c` refuse to load without C. `T+ preview` and `option E placeholder` rows refuse to freeze; regenerate the matrix from `e2e-sources.json` first.
- Every arm of a slot is prepared first: secrets and barrier folders. The arms are then spawned back to back in the frozen launch order. The next slot starts only after every arm has exited, been cleaned up and been collected. A failing arm never cancels its siblings.
- `dispatch_skew_s` is the spread of host launch times on the monotonic clock. If it exceeds 1 s, every arm in the slot becomes invalid and the unit stops with `dispatch_skew_exceeded`.
- `agent_start_skew_s` comes from Harbor `agent_execution.started_at`. A spread above 30 s sets only `pair_sync=false`. Such a pair still counts for success and recovery and is left out of within-pair latency.
- `--infra-preflight` first pulls each agent image and builds each task's verifier image once, serially, skipping images already present, so no slot builds the same image in two children at once.
- `--barrier` is optional. `slot_agent:SlotBarrierHandoffAgent` waits for its peers at the end of `setup()`, inside the 600 s setup budget and outside the 570 s agent budget, for at most 120 s. It records `<arm>.json`.
- An infrastructure-invalid arm stops the unit after its siblings finish (`infrastructure_invalid_arm`). Semantic failures continue. Trials are never retried.

## Guards

Every guard runs before each slot. Guard bookkeeping after each slot always runs, even when the slot stopped the unit.

- Host lock: `fcntl.flock` on `<run-root>/.execution-lock` in mode `e2e-slot`. It is held for the whole unit and checked around every slot. A held lock gives `schedule_overlap`, which is infrastructure invalid. Events go to `.execution-lock.log.jsonl`.
- Account: the runner reads fp12 = sha256(`tokens.account_id`)[:12], the plan claim and the access-token expiry. It never prints or stores tokens. The unit must match G0 (`anonymous-account-02`, `prolite`). The margin must be at least the remaining slots x 1050 s + 3600 s. Refusal classes are `account_unreadable`, `account_changed` and `auth_expiry_margin`.
- Quota: the unit starts only if used% + r x planned calls / 100 is at most 90%. Otherwise the decision is `pause-reset`, or `no-snapshot` when no reading is recent enough. A unit planned above 300 Astra calls takes one mid-unit reading, and 95% or more stops it (`quota_stop`). Readings come from `--quota-snapshot` (operator `/status`). `--quota-live` uses `core.llm.codex_oauth_usage.fetch_codex_usage` only when the user has approved that lookup. Window labels are not trusted: the highest used% over the present windows counts.
- Jev budget: the host ledger `jev-cost-ledger.jsonl` admits the unit and reserves the frozen per-trial cap (`jev_call_cap`, 9 for arms B and C, derived from the pinned source by `run_guards.derive_jev_call_caps`) x 25k input tokens per Jev arm before launch. After collection it settles the observed calls, and unknown counts settle in the reserve column. The authorized budget amendment sets $2.115 to start, $2.2325 to stop and a $2.35 cap, preserving the prior ledger chain. Refusal and stop classes are `jev_ledger_unavailable` (before the unit), `jev_budget_refused`, `jev_budget_exhausted` and `jev_ledger_error`. More observed calls than the cap in one trial is a `reservation_overrun`, which stops the program ledger by the ledger's design.
- Operator stop: a `<phase>/STOP` file refuses the next slot (`operator_stop`).

## Records

- `trials/<trial>/trial-receipt.json`, `attempts.jsonl` (every attempt selected, contiguous sequence), `slots.jsonl`, `results.json` and `analysis.json`. The analysis is validated with `scripts.eval.contract.validate_analysis`.
- `private-receipts/<attempt_id>.json` (mode 0600, `jev-v3.private-trial-receipt@1`) records:
  - the canonical columns `slot_id`, `dispatch_skew_s`, `agent_start_skew_s`, `pair_sync`, `concurrent_trials` and `external_account_usage="unknown"`
  - account fields: fp12, plan and expiry margin
  - the quota checkpoint
  - the Jev reservation and settlement
  - the freeze digests
  - validity and outcome

  The runner does not write `overlapping_calls`; the data tables derive it.
- Freeze cells carry `policy_digest`, `reset_digest`, `case_sha256`, `task_checksum` and `verifier_sha256`. Repetitions combine only when these are equal.
- An incomplete unit has a primary of `not-measurable`, and every planned-cell outcome is kept.

## Sources (option E)

`make_tasks.py` is run by the holder of sealed-source access, never by the runner. It reads `e2e-sources.json` (option "E") and checks:

- the salt: sha256 of the sorted source-file digests
- the ranks: 1-12 natural, 13-18 injected with the three cells, 19-20 spare
- every file digest
- the admission rows `FILE#cluster_id` at selection ranks 14 and 15, when the selection manifest is given

It stages the pinned r6 task writer and writes the following:

- `payloads/`
- `task-bundle/`
- `labels.jsonl` (0600)
- `payload-manifest.json`, which lists workloads, digests and the ordered ids. It carries no gold.

## Steps

1. `runner.py --pin-source --source <clean checkout> --revision <sha>`. This runs once and never overwrites.
2. The sealed-access owner runs `make_tasks.py --sources ... --sources-root ... --slots e2e-slots.jsonl --selection-manifest ... [--units ...]`.
3. `runner.py --self-test`. It is model-free and uses mock arms.
4. `runner.py --infra-preflight --concurrency 2|3 --reviewed`. This uses Docker only and no model, and the proof is valid for 24 h.
5. `runner.py --quota-snapshot --used-pct P --checkpoint ID`.
6. `runner.py --freeze --unit U --run-spec F --bundle B [--arm-c --selection-freeze S] [--barrier] --reviewed`, then `--preflight --unit U`.
7. With live approval, `runner.py --execute --unit U --reviewed`. After an admission unit, reviewed `playback-check.json` must exist before a dependent unit can freeze.
