# Legacy GEODE checkpoint-store retirement receipt

Date: 2026-07-21

Disposition: retain a sanitized receipt; do not publish the raw database

## Decision

The audited `geode_checkpoints.db` file was a retired runtime state store, not an
evaluation result. The raw SQLite database is therefore excluded from this
public repository. This receipt preserves the evidence needed to identify and
reason about the store before the audited copy was retired:

- a SHA-256 identity and source timestamp;
- SQLite integrity results, schema shape, row counts, and payload sizes;
- per-thread aggregate counts without checkpoint contents;
- the runtime-consumer audit and the retention rationale.

The raw file contains opaque MessagePack state snapshots and channel writes.
Those values may include complete model/tool state and do not have a public
redaction contract. Publishing them would violate this repository's
minimal-evidence rule: durable verifier outputs belong here; transient runtime
state and reproducible scratch do not.

## Source identity

| Field | Value |
|---|---|
| Original filename | `geode_checkpoints.db` |
| Size | 2,015,629,312 bytes |
| SHA-256 | `6130fd7158c890beee9db7c41e54f563c2c0453a3ca6fe720a1150189735bee1` |
| Last database write | `2026-05-15T05:38:43Z` |
| SQLite integrity | `PRAGMA quick_check = ok`; `PRAGMA integrity_check = ok` |
| Audited GEODE remote revision | `94b6b87c0710ac2ae5c40fc25cc8838466ff75ed` (`origin/main`) |

The source path and workstation username are intentionally omitted. The hash is
the stable identity for any independently retained copy.

## Aggregate inventory

| Metric | Value |
|---|---:|
| Page size / page count | 4,096 / 492,097 |
| Free pages | 0 |
| Checkpoint rows | 2,461 |
| Checkpoint payload | 1,274,924,228 bytes |
| Checkpoint metadata | 232,183 bytes |
| Write rows | 20,271 |
| Write payload | 727,593,131 bytes |
| Threads / checkpoint namespaces | 7 / 1 |
| Write channels | 42 |

All non-empty payloads use the `msgpack` serialization label. Of the write
rows, 15,905 carry 727,593,131 bytes and 4,366 carry a null/empty payload.

| Thread | Checkpoints | Checkpoint bytes | Writes | Write bytes |
|---|---:|---:|---:|---:|
| `ip:cowboy_bebop:analysis` | 2,313 | 1,266,294,304 | 19,064 | 722,727,835 |
| `ip:hollow_knight:analysis` | 42 | 3,285,855 | 333 | 1,738,824 |
| `ip:berserk:analysis` | 45 | 2,092,485 | 384 | 1,258,073 |
| `ip:dead_cells:analysis` | 19 | 1,251,962 | 159 | 744,164 |
| `ip:hades:analysis` | 22 | 1,189,572 | 169 | 623,711 |
| `ip:repo:analysis` | 11 | 549,960 | 85 | 325,044 |
| `ip:ghost_in_the_shell:analysis` | 9 | 260,090 | 77 | 175,480 |

The `cowboy_bebop` thread accounts for 99.3261% of checkpoint-plus-write
payload bytes. The store is therefore one historical analysis trace with six
small companion traces, not a shared current-runtime database.

## Runtime-consumer audit

At the audited GEODE `origin/main` revision, `git grep` finds no
`geode_checkpoints.db` or `checkpoint_db` consumer under `core/` or `plugins/`.
Commit `c4deb54848e39ff4615d3f856d75286ed864955e` removed `checkpoint_db` on
2026-06-15 as a vestigial setting that had no runtime reader. The database's
last write predates that removal by one month, and no process held the database
open during retirement inspection.

Current checkpoint-producing paths use scoped stores with explicit retention
or run-local JSON checkpoints; this SQLite file cannot resume those paths.

## Retention rationale

The agent-engineering review applied four tests:

1. **Operational reachability:** failed. Current code has no reader or resume
   path for this file.
2. **Evaluation provenance:** failed. The rows are runtime state, not verifier
   verdicts or a cited benchmark run directory.
3. **Public safety:** failed closed. Opaque state snapshots cannot be proven
   free of private prompts, tool results, or local context through a metadata
   scan alone.
4. **Storage proportionality:** failed. A 2.0 GB raw state store would impose
   permanent public-repository cost while 99.3261% of its payload belongs to a
   single retired trace.

The selected policy is therefore **receipt-only retirement**. If a separately
retained private copy is encountered later, its SHA-256 can be matched against
this receipt; this public repository does not need the payload itself.

## Trajectory consequence

This receipt is not a trajectory dataset or a replayable backup. It records
identity, aggregate shape, integrity, and disposition, but no row-level
checkpoint transitions.

A current source scan did not locate the audited 2,015,629,312-byte payload
with SHA-256
`6130fd7158c890beee9db7c41e54f563c2c0453a3ca6fe720a1150189735bee1`.
A same-named 692,224-byte local SQLite file is not a surviving copy: its
SHA-256 is
`b96d1660b37d33986eb2bc3c9d1c2c2d002e607a8db75e7e7ac57665ebf551ea`,
and `PRAGMA quick_check` reports malformed B-tree pages.

The historical `cowboy_bebop` process is only partially reconstructable from
separate telemetry, snapshot metadata, result variants, and one related
session. Those surviving sources and their non-additive counts are catalogued
in the
[2026-07-21 trajectory inventory](../trajectory-inventory/2026-07-21.md#legacy-cowboy-bebop-checkpoint-trace).
Any derived trajectory must mark missing checkpoint transitions rather than
imply exact replay.

## Related local cleanup

The same audit compared all 408 ignored local Petri `.eval` logs against
`sil/petri-audits/` by filename and byte content. All 408 files, totaling
91.0 MiB, matched exactly. No second upload is required; the local duplicates
can be removed while this repository remains the canonical copy.

The machine-readable companion is
[`2026-07-21-geode-checkpoints-retirement.receipt.json`](./2026-07-21-geode-checkpoints-retirement.receipt.json).
