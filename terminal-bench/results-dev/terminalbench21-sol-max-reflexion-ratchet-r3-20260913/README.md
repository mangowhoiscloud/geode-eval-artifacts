# terminalbench21-sol-max-reflexion-ratchet-r3-20260913

Terminal-Bench 2.1 `gcode-to-text`: five fresh trials of one GEODE candidate.
The run settings are in [`run-spec.json`](run-spec.json) and the five job specs
(`job-candidate-r*.json`).

**Result:** 5 of 5 attempts valid and passed by the official verifier
([`attempts.jsonl`](attempts.jsonl), [`verifier-receipts.json`](verifier-receipts.json),
`raw/live/candidate-r*/*/verifier/`).

**Bound:** a development diagnostic. It is not a full-suite score, a held-out
result or best-of-five selection, and it claims no causal improvement
([`ACCEPTANCE.md`](ACCEPTANCE.md), [`analysis.json`](analysis.json)).

Cited by the GEODE Terminal-Bench page, section "2026-09-13 full-runtime G-code
development gate":
<https://mangowhois.ai/products/geode/docs/benchmarks/terminal-bench/>.

## What is published

[`publication.json`](publication.json) lists every file here with its SHA-256
and the SHA-256 of the source it came from (a private verified backup).
`trial_uri` in the five trial `result.json` files is masked as
`redacted://harbor-trial/<trial>`; nothing else was changed.

Withheld, following [TRAJECTORIES.md](../../../TRAJECTORIES.md): agent
sessions, runtime state and trajectories (not reviewed for publication),
terminal recordings, harness logs and configs, the task dataset snapshot, a
canary task fixture, preflight archives, helper scripts and draft specs. The
published receipts keep the digests of those files.
