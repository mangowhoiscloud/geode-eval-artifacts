# tau2 1.0.1 three-domain diagnostic

- GEODE: `8a5c26454e11c3d6240a772a8a40277781b77789`
- Agent: `gpt-5.6-terra`, OpenAI subscription route, `max`
- Simulated user: `gpt-5.5`, OpenAI subscription route, `high`
- Harness: `sierra-research/tau2-bench@79975ac5741e23fbb1d2ac44262d62398a6d87bd`
- Preflight receipt SHA-256: `ef28eed9b5490efe1fe585889ac04c2653af0991c151d04460576db6d861d3be`

| Domain | Task | Duration | Termination | Reward |
|---|---|---:|---|---:|
| Airline | `0` | 63.93 s | `user_stop` | 1.0 |
| Retail | `0` | 103.58 s | `max_steps` | 0.0 |
| Telecom | `mobile_data_issue / roaming off` | 86.83 s | `max_steps` | 0.0 |

Mean native reward is **1/3 = 0.3333**. The selected runs used 274,134 input
tokens, 9,413 output tokens, and 137,216 cache-read tokens; message-level cost
estimates sum to `$0.6378085`.

The first Retail attempt failed before evaluation on a provider connection
timeout and is retained as infrastructure-invalid lineage. A Telecom loader
attempt also failed before a provider call because the frozen task belongs to
the upstream `full`, not default `base`, split; the selected run names that
split explicitly. Neither incident replaces or alters the two valid zeroes.

The public copy retains selected native simulations, retry evidence, runtime
profiles, and normalized trajectories. Synthetic benchmark names and account
identifiers are fixtures, not real customer data. Private event bodies remain
digest-projected, so the trajectories are scope-complete but not byte-replay
complete.
