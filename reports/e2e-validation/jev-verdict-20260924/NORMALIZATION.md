# Public normalization and evidence boundaries

## Source and output identities

M4 and M5 executed GEODE `1c73cb97657dc811264bea338aa5a2ae324f0078`.
M6 and its reused admission executed
`588a1c8817d6cff83f8acc0c9e5187d91ccafe60`. The normalizer's GEODE revision
is a separate field: a newer publication/privacy implementation does not
retroactively become the measured runtime.
The receipt also binds the actual trajectory, release, redaction and contract
implementation files. A supplied Git revision alone does not attest that an
uncommitted worktree used identical bytes.

The source bundle, frozen specification, append-only attempt ledger,
provider records, independent oracle, and published projection have distinct
identities. `normalization-receipt.json` records each source's relative name,
byte count and SHA-256 beside the derived public SHA-256, removed JSON
pointers and declared reference changes. It also binds the separately
validated **private admission manifest** and inventory of withheld bytes.
No source run file is modified. Two removed worktree references in the M4
freeze are rebound to members of the original pinned archive only after
their member bytes match the recorded frozen hashes.

## Producer, retained surface and reader

| Producer | Public surface | Reader / purpose | Withheld or bounded |
|---|---|---|---|
| Prospective runner | `source-contract.json`; source digest | Original question, models, task/infra pins and analysis scope | This is not the later retrospective public `run-spec.json`. |
| Harbor / runtime | Projected native `result.json`, `trial-receipt.json` | Native reward, validity, termination, timing and exact accounting fields | Raw configuration, local paths, candidate/tool bodies and opaque exceptions are removed. |
| Independent oracle | `verifier-receipt.json` | Outcome checks and component matches | Answer bodies are withheld; retained booleans are native observations, not a fresh regrade. |
| Final-verdict adapter | `verification.json` / snapshot `native.json` | Engine, input/question hashes, labels, native Jev distribution, correlation and feedback hashes | No hidden reasoning, generated rationale or root system prompt. Code-owned feedback authorship is preserved. |
| Controlled replacement seam | `intervention.json` | One injection's timing, call identity and native/effective content hashes | Native/effective bodies stay private; no invented natural failure. |
| Usage observer and collector | Usage/call-accounting fields; observation checks | Token coverage, missing values, response latency, tariff/API-equivalent accounting | Actual charge remains null without invoice evidence. |
| Attempt and analysis owner | Retrospective `attempts.jsonl`, `analysis.json` | Valid/invalid outcomes and digest-bound primary denominators | References bind the derived files, not falsely the original bytes. |
| Existing trajectory exporter | Separate `geode.trajectory@1` releases | Ordered visible event kinds, tool pairs and source-digest joins | Content digests do not provide executable byte replay. |

## Deterministic preparation

`normalize.py` takes the operator-supplied private source root, a fresh public
repository worktree, fixed preparation timestamp, artifact base revision and
GEODE normalizer revision. It has no model-dispatch or credential-loading
path. File-level keys and nested metadata text fields are closed for review;
private bodies and machine-local
locations are removed by explicit field rules. Non-JSON references become
named `.withheld.json` receipts rather than masquerading as database or
transcript files. Source/public identities never share a digest by assertion.

The private source manifest is validated using the original GEODE checkout
and its existing run record. The public manifest is validated with the
publication implementation and dated run record. No symlink or duplicated
private source tree is used to satisfy the validator's source lookup.

The normalizer uses GEODE's existing owners:

1. `scripts.eval.contract.validate_run_bundle` before projection and again
   after new retrospective sidecars and derived hashes are written.
2. `verify_trajectory_integrity`, `stage_trajectory_release` and
   `verify_trajectory_release` for scope, schema, identity, content digests,
   privacy review and append-only release directories. Replay completeness
   is explicitly not required for these digest-projected public traces.
3. `validate_publication` for every declared byte count, digest, classification
   and destination. Separate trajectory manifests bind their own bytes.
4. Provider-key, bearer-token, email and local-path scans over public files;
   these supplement payload review and are not a proof of universal privacy.

The publication manifest covers the normalizer and all report files except
itself. `normalization-receipt.json` binds the two independent trajectory
manifests. The fixed timestamp makes regeneration comparable before upload;
already staged trajectory directories are verified and never overwritten.

## Non-goals and remaining publication steps

This projection creates no new benchmark score, deployment approval, invoice
reconciliation, calibration estimate, or training admission. The three authored
inbox cases and small controlled conditions are diagnostic. Predecessor failures
remain visible, and no primary metric pools them with valid task outcomes.

Prepared files still require independent privacy/diff review, a repository
PR, immutable remote read-back and a GEODE run-record update. A local green
validator is not evidence that these publication steps have happened.
