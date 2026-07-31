# Trajectory publication contract

This repository distinguishes replayable trajectories from score receipts and
forensic summaries. A file is trajectory-capable only when it preserves an
ordered sequence of state transitions or actions and enough provenance to
interpret the outcome. Aggregate counts and hashes can prove that a source
existed without making that source a trajectory.

The current source inventory is published as both a human-readable report and
a machine-readable manifest:

- [`reports/trajectory-inventory/2026-07-21.md`](reports/trajectory-inventory/2026-07-21.md)
- [`reports/trajectory-inventory/2026-07-21.json`](reports/trajectory-inventory/2026-07-21.json)

## Record classes

| Class | Minimum retained structure |
|---|---|
| `dialogue` | Ordered user, assistant, and environment messages |
| `tool` | Ordered tool calls and results with stable pairing |
| `search` | Candidate or mutation, evaluation, decision, and lineage |
| `decision` | Ordered policy, evidence, approval, or termination events |
| `retirement_receipt` | Aggregate identity and disposition only; **not a trajectory** |

One source can support more than one trajectory class. For example, a tau2
episode is both a dialogue and tool trajectory, while an autoresearch run is a
search trajectory even when it is not conversational.

## Schema and identifier rules

New GEODE trajectory publications use the stable
`geode.trajectory@1` record contract and
`geode.trajectory-release@1` manifest contract. Schema versions change only
for a breaking wire-format change; publication identity remains a UTC
timestamp plus a content digest. Mutable labels such as `latest` and retry
suffixes are never release identity.

- Calendar date: ISO 8601 `YYYY-MM-DD`.
- Timestamp in metadata: RFC 3339 UTC `YYYY-MM-DDTHH:MM:SSZ`.
- Timestamp in a path or identifier: colon-free UTC
  `YYYY-MM-DDTHHMMSSZ`.
- Inventory pair:
  `reports/trajectory-inventory/YYYY-MM-DD.{md,json}`.
- Release identifier:
  `<source>-<scope>-<published-utc>-<manifest-sha256-prefix>`.
- Current trajectory schema identifier: `geode.trajectory@1`.
- Current release manifest identifier: `geode.trajectory-release@1`.
- Inventory schema identifier: `geode.trajectory-inventory@YYYY-MM-DD`.

The digest prefix is the first 12 lowercase hexadecimal characters of the
full SHA-256 recorded in the manifest. A correction is a new immutable
release with a later UTC timestamp, a new digest, and a `supersedes` pointer.
The earlier release remains addressable.

Published dated schemas such as `geode.trajectory@2026-07-31` remain immutable
legacy evidence. Readers may normalize their `sequence`/`timestamp` fields to
`ordinal`/`occurred_at` in memory, but must never rewrite those releases.
Source-native historical identifiers are also preserved verbatim for
provenance.

The three time fields have distinct meanings:

- `captured_at`: when the source event or run occurred.
- `observed_on`: the UTC calendar day on which an inventory was measured.
- `published_at`: when an immutable public release was created.

Unknown times are `null`; they are never inferred from file modification time
without saying so in provenance.

## Normalized envelope

A current normalized trajectory is JSON and defines:

- `schema_id=geode.trajectory@1`, `schema_version=1`, `trajectory_id`, and
  `trajectory_class`;
- `source` with harness, run, task, session, and parent identifiers when
  available;
- `captured_at`, `observed_on`, and `published_at`;
- ordered `events`, each with a contiguous one-based `ordinal`, stable unique
  `event_id`, `occurred_at`, `actor`, `kind`, `session_id`, `turn_id`,
  `call_id`, and payload or payload digest;
- `outcome` with verifier, reward, terminal state, or an explicit
  `unscored` reason;
- `provenance` with source revision, adapters, model route, and extraction
  transform;
- `privacy` with review state, redaction actions, and license status;
- `integrity` with independently recomputable record count, correlation and
  tool-pair quality, separate `scope_complete` and `replay_complete` states,
  and typed incompleteness reasons;
- optional content-bound `runtime_event_refs`, `evidence_refs`, and
  `artifact_digests` that point to a source authority without copying its
  private bytes.

Tool trajectories require stable call/result identifiers and exact pairing.
Search trajectories require parent candidate lineage so train, validation,
and test partitions cannot contain descendants of the same campaign on both
sides.

## Storage authority and public bundle

The normalized trajectory is a portable evaluation view, not a replacement
for the producing system's native evidence:

- GEODE session history remains authoritative in
  `sessions.db:session_events`; `events.jsonl` is a bounded run projection.
- SIL keeps its Inspect `.eval`, mutation ledger, attribution ledger, and
  native verifier outputs authoritative.
- Crucible keeps `crucible.evidence.v3`, frozen assay contracts, tau2 native
  simulations, verifier receipts, and campaign state authoritative.
- MCPMark and tau2 retain their native result/receipt directories. A GEODE
  trajectory joins them by stable identifiers and verified digests.

A public native-receipt copy may require field-aware masking. That public copy
is a privacy-preserving projection, not a silent replacement for the restricted
native source. The trajectory and producer snapshot retain the verified raw
source digest; the publication record separately reports the public-copy
digest and the applied redactions.

A current public release directory contains exactly:

- one or more allowlisted `geode.trajectory@1` JSON files;
- one `geode.trajectory-release@1` `manifest.json`.

SQLite databases and WAL files, mutable checkpoints/messages, raw run JSONL,
provider diagnostics, usage ledgers, hidden reasoning, private prompts, and
unreviewed tool bodies are not release members.

The manifest binds file sizes, SHA-256 digests, trajectory identities, record
counts, scope/replay completeness, privacy review, secret-scan counts, and
source-digest verification. Its directory suffix is the first 12 characters
of the manifest SHA-256. Remote consumers should pin the full manifest digest,
not merely trust a self-consistent directory.

## Availability labels

- `published`: already present in this public repository and usable within
  the trajectory class stated in the inventory.
- `review_required`: locally retained and potentially useful, but needs
  redaction, normalization, licensing, or join validation.
- `restricted`: useful only under an explicit allowlist or private storage
  policy because it contains general runtime context or sensitive state.
- `excluded`: not eligible for a trajectory release, such as raw chain of
  thought, credentials, private MCP data, corrupt files, or unredactable
  checkpoint payloads.

Availability is not a quality score. A published tool trace may still lack the
model dialogue needed for a dialogue trajectory.

## Publication lifecycle

1. **Inventory:** count physical records, content-unique records, outcomes,
   and known overlaps without copying private payloads.
2. **Normalize:** convert the source into the stable `geode.trajectory@1`
   schema while preserving
   source identifiers and ordering.
3. **Redact:** remove credentials, personal data, local absolute paths,
   private prompts, and unnecessary tool payloads. Redactions are typed and
   counted rather than silently erased.
4. **Validate:** parse every record; verify event order, call/result pairing,
   outcome joins, canonical uniqueness, and parent lineage.
5. **Split:** partition by task, session, and campaign lineage, not random
   rows, to prevent rerun and descendant leakage.
6. **Publish:** require a structured scope-bound privacy attestation; write an
   immutable manifest; compute SHA-256 digests; push the release; and read it
   back from the remote against an independently retained manifest digest.
7. **Retire:** delete a unique local source only after the destination,
   manifest, counts, and remote read-back are verified, or after a documented
   decision that the source is excluded and no extraction is required.

This gate intentionally prevents a retirement receipt from being mistaken for
a backup. A receipt supports provenance and deletion auditing; it cannot
reconstruct row-level state.

## Safety boundaries

- Do not publish raw reasoning diagnostics or hidden chain-of-thought.
- Do not bulk-publish general runtime sessions. Export only allowlisted
  task-scoped sessions after payload-level redaction.
- Treat tool inputs and results as sensitive even when model text is clean.
- Treat checkpoint databases as restricted containers, not datasets. Extract
  only through a field-aware decoder and retain no opaque payload by default.
- Preserve verifier outputs and rewards separately from model-authored
  claims.
- Record truncation. A compact transcript with shortened tool payloads is a
  lossy tool trajectory and must not be described as full fidelity.
- Verify third-party dataset and harness licenses before redistributing
  locally retained copies.

## Minimum release checks

A release is not complete until all applicable checks pass:

- all JSON or JSONL records decode;
- declared counts equal recomputed counts;
- trajectory identifiers are unique;
- event ordinals are contiguous, event identifiers are unique, required
  session/turn/call correlation is present, and tool calls pair with results;
- outcome joins have no unexplained orphans;
- lineage-aware split checks pass;
- secret, credential, email-like, and absolute-path scans are reviewed;
- scope completeness is true; any replay reduction is explicit and admitted;
- every source digest is checked against actual source bytes before staging;
- when a native receipt is publicly redacted, raw-source and public-copy
  digests are both recorded and never presented as byte-identical;
- the directory contains no files absent from the manifest;
- every published file has a SHA-256 entry and the privacy review record is
  content-bound;
- the remote copy can be fetched and its manifest digest matches an
  independent anchor.

The dated inventory records what exists. It does not itself authorize
publication or deletion of any local source.
