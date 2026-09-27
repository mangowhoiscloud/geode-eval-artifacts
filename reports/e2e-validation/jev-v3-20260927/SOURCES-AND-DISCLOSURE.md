# Sources and disclosure

This is a reviewed disclosure of the Jev v3 study's retained measurements.
The public files are projections with their own SHA-256 digests. Embedded
native digests continue to identify the retained originals; a redacted
projection is not a byte-identical original.

GEODE runtime and analysis code is attributed to the
[GEODE repository](https://github.com/mangowhoiscloud/geode) at the revision
recorded for each unit. Its [Apache-2.0 license](study/GEODE-LICENSE.txt)
continues to apply to that code. Exported driver source is an archival,
identity-redacted copy and may need operator path and account configuration
before a new run. The offline recomputation command described in
[REPRODUCE.md](REPRODUCE.md) uses the pinned native analysis owner.
This packet does not relicense upstream datasets or third-party material.

X1 is derived from the
[Microsoft CUAVerifierBench dataset](https://huggingface.co/datasets/microsoft/CUAVerifierBench/blob/c19eb323cd802add5c3d2840ff13044061364867/README.md),
whose dataset card specifies MIT. The public X1 view preserves label, vote,
source/split and measured-prediction metadata. Read the input transformation
and its information-loss boundary before comparing with the original benchmark.

X2 is derived from [OSU-NLP-Group Mind2Web](https://github.com/OSU-NLP-Group/Mind2Web/blob/33bd95caeee7bba22dd08ecc935845e15c5e5dc7/README.md#dataset-access).
Its maintainers request that unzipped test data not be redistributed online.
This packet therefore publishes identifiers, labels/grades, split/site and
structural metadata, source and conversion hashes, outcomes and analyses;
it excludes the original test questions, action text, raw/cleaned HTML,
candidate bodies and source archive. The pinned
fetch/conversion source is included for a reader to reacquire inputs from the
official distribution under its terms. Whole web-task success is not measured
by this four-candidate text-only transformation.

Synthetic panel/task inputs and previously approved unsealed label exports
are included with their provenance. They are disclosed study inputs and must
not be treated as unseen holdouts in a future evaluation.

The [numeric-response disclosure](corrections/numeric-parser-20260928/numeric-response-disclosure.json)
adds 1,280 reviewed numeric-only U4/X2 parser inputs, bound to retained
dispatch hashes, rows and JSON pointers. This permits pointwise response
re-parsing without publishing task/candidate bodies, model reasoning or full
provider transcripts. Its scope and the retained Astra listwise-winner
boundary are documented in [REPRODUCE.md](REPRODUCE.md).

The additive [U8n post-hoc disclosure](analyses/u8n-observed-pairs-20260928/README.md)
contains only the final visible candidate state for each of 22 complete-valid
paired trials. Its task contract and request match the authored synthetic
inbox and already disclosed payloads; its lookup observations contain synthetic
order IDs and statuses. The separate source/public map identifies the exact
native JSON pointers and public row digests. It does not restore the full
verification history, ambient system prompt, private reasoning or provider
transcript excluded by the original E2E exporter.

Credentials, auth files, account identifiers, private reasoning/provider
transcripts, private environment state and unopened sealed source folders
are excluded. Exclusion and projection records are present in the component
source maps. The video, its music and unpublished raw screen
recordings are outside this data release.
