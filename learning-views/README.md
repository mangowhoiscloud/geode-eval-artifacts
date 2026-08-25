# GEODE learning views

Versioned, immutable projections over native evaluation output. The raw
producer formats remain authoritative; these views provide a stable join:

```text
example -> rollout -> geode.trajectory@1 -> reward
```

`v2/` separates workload identity, policy execution, behavior evidence, and
evaluator output. A retry extends `rollout_attempt_ids`; it never creates a new
rollout or replaces an infrastructure-valid zero. Reward rows point back to an
exact native JSON value by path, SHA-256, and JSON Pointer.

## Releases

| Run | Scope | Native result |
|---|---:|---:|
| `terminal-bench-2.1-geode-gpt-5.6-terra-max-fast3-20260825` | 3 tasks, k=1 | 3/3 |
| `tau2-1.0.1-geode-gpt-5.6-terra-max-3domain-20260825` | Airline, Retail, Telecom; one task each | 1.0, 0.0, 0.0 |

Both are subscription-route diagnostic pilots with no leaderboard or release
promotion authority.
