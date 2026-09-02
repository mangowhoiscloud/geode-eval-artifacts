# Same Model, Different Harness

## GEODE vs Native Codex on Terminal-Bench 2.1

This document is the source of truth for the short instruction and research-design
opening of the live verification video. The benchmark run remains the main content.

## 1. Opening instruction — 0:00–0:18

### On-screen copy

> This is a verifier-backed Terminal-Bench 2.1 run.
>
> KST is shown on screen. UTC is the canonical evidence clock.
>
> Observer-side PTY captures recorded the Harbor runner and batch progress while
> the run was active. ATIF-derived segments are explicitly labelled as reconstructed
> replays and linked to their source trajectory hashes.

### Viewer guide

- `VALID · 1` — the canonical verifier passed.
- `VALID · 0` — a semantic failure or protocol-correct timeout; it remains zero.
- `INFRA-INVALID` — no score is selected; only preregistered missing cells may be supplemented.
- Every task result is traceable to a run spec, result file, verifier receipt, trajectory, and SHA-256 hash.

## 2. Evaluation design — 0:18–0:52

### Research question

When the model and benchmark protocol are held fixed, how does the GEODE harness
compare with the native Codex harness on Terminal-Bench 2.1?

### Paired design

```text
Terminal-Bench 2.1 · 89 tasks · 5 repetitions
                         │
         same model · same effort · same task contract
                         │
            ┌────────────┴────────────┐
            │                         │
          GEODE                  Native Codex
            │                         │
            └──────── canonical verifier ────────┘
                         │
      pass / 445 · paired delta · paired contingency
```

### Frozen controls

- Model: `gpt-5.6-sol`
- Reasoning effort: `max`
- Dataset: Terminal-Bench 2.1, registry revision `@6`
- Harness authority: Harbor `0.22.0`
- Repetitions: five per task and arm
- Automatic retries: zero
- Timeout multiplier: `1.0`
- Container, task digest, verifier, timeout, CPU, memory, and storage: task-specific and frozen
- Concurrency: one for 8192 MiB tasks; otherwise the frozen resource-valid batch value
- Seeds: unsupported by Harbor `0.22.0`; repetitions are workload-aligned, not shared-randomness pairs

### Selection rule

- Semantic failures and canonical timeouts are selected reward zero.
- Auth, provider stream, container admission, digest, verifier-authority, or budget-enforcement failures are infrastructure-invalid.
- An infrastructure-invalid cell may receive one prospective, preregistered supplement.
- All original and supplemental attempts remain in the lineage.

### Claim boundary

The frozen direct paired full-suite estimate required exactly 445 selected cells in
each arm. That condition was not met, so the video withholds the primary estimate and
reports secondary observed coverage plus the exact common-cell comparison. Public
leaderboard values are not presented as an equivalent score or rank.

## 3. Live run chapter — main body

Each recorded segment uses the same compact header:

```text
TASK 25 / 89                       KST 21:24:37 · UTC 12:24:37Z
GEODE · repetition 5 / 5           Harbor 0.22.0 · retry 0
```

The video shows all 67 preserved observer capture files. Sixteen replay as valid
timestamped PTY records. Fifty-one contain invalid timestamp streams; only printable
text is recovered from those files, timing is not asserted, and the limitation is
visible on every affected frame. These are procedure evidence, not Harbor-native
trial recordings or score authority.

Where an ATIF trajectory exists, Harbor-compatible `recording.cast` is reconstructed
with the merged renderer at GEODE revision `475507ff0815862bb04dee789e1e094823b4dc0f`.
Each cast is labelled `trajectory-reconstruction`, digest-bound to the ATIF source,
and withheld from the public derivative until separate privacy review.

At completion, the result frames show only:

```text
VALID · reward 1.0
result ✓  verifier ✓  trajectory ✓  hashes ✓
```

No provider reasoning, credentials, account identity, PII, or local absolute path
appears in the public derivative.

## 4. Closing evidence — final 20–30 seconds

Show, in order:

1. Primary metric: not measurable under the frozen 445-per-arm rule.
2. Secondary observed coverage: GEODE `344/435`, native Codex `331/429`.
3. Exact common cells: GEODE `339/429`, native Codex `331/429`.
4. Paired contingency: both pass 286, GEODE-only 53, native-only 45, both fail 45.
5. Two symmetric task exclusions and six unresolved native infrastructure-invalid cells.
6. Artifact publication path, digest validation, comparability boundary, and limitations.

Do not show a final score until the publication manifest and remote readback agree.

## 5. Visual and pacing rules

- 1920 × 1080, 60 fps.
- Black background, white text, one restrained accent color.
- Menlo for terminal content; Pretendard for Korean guidance.
- One evolving paired-design diagram; no card grid and no decorative transitions.
- Opening instruction: 18 seconds.
- Research design: 34 seconds.
- Terminal evidence: the rest of the video, accelerated only during silent waits.
- Never accelerate command entry, task identity, verifier summary, or receipt frames.
- ATIF reconstructions carry `DERIVED REPLAY · NOT RAW PTY` throughout the segment.
- Valid observer records carry `RECORDED LIVE · OBSERVER EVIDENCE`.
- Damaged records carry `INVALID TIMESTAMP STREAM · RECOVERED TEXT`.

## 6. Acceptance checklist

- [x] KST is visible; UTC `Z` is preserved in the evidence ledger.
- [x] Observer and reconstructed segments cannot be confused.
- [x] Every shown reward matches the canonical verifier receipt.
- [x] Every shown local hash matches its source artifact or receipt.
- [x] No secret, PII, provider reasoning, or host-local absolute path is visible.
- [x] The primary score is withheld because the frozen coverage rule was not satisfied.
- [x] The upload-ready MP4 plays end to end at 1080p60.

## Reference boundary

The reference paper-seminar video informs only the simple research narrative:
question, design, evidence, result, and limitations. Its visual identity, slide
design, and wording are not copied. Frame and caption analysis was unavailable due
to source throttling, so no pacing claim is inferred from unseen material.
