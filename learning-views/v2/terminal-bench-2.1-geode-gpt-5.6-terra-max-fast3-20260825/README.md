# Terminal-Bench 2.1 fast-3 diagnostic

- GEODE: `8a5c26454e11c3d6240a772a8a40277781b77789`
- Model: `gpt-5.6-terra`, OpenAI subscription route, `max`
- Harness: Harbor `0.8.0`, `terminal-bench-2-1@6`
- Dataset SHA-256: `7d7bdc1cbedad549fc1140404bd4dc45e5fd0ea7c4186773687d177ad3a0699a`
- Tasks: `fix-git`, `openssl-selfsigned-cert`, `build-pmars`
- Result: **3/3**, no exceptions, k=1
- Wall time: **602 seconds**
- Usage: 459,406 input tokens; 18,565 output tokens; Harbor cost estimate `$0.745006`

All three tasks passed their Oracle preflight before the GEODE run. The public
copy retains each native result, verifier output, and normalized
`geode.trajectory@1` file. The three trajectories contain 74 events and 25
exact tool call/result pairs with zero orphans. Private payload bodies are
digest-projected, so replay fidelity is intentionally reduced.

This three-task pilot is not an official Terminal-Bench score and is only
directionally comparable to the full 89-task leaderboard.
