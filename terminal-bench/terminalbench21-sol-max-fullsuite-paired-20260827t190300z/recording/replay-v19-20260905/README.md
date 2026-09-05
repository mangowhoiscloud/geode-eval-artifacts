# GEODE / Codex paired execution replay

This is a derived, public presentation view of the frozen Terminal-Bench 2.1
run `terminalbench21-sol-max-fullsuite-paired-20260827t190300z`, not a new
measurement or a raw PTY recording. GEODE revision:
`b549f3e448f06c75db45df6082013dc21a611dec`; both arms used the OpenAI subscription
route, `gpt-5.6-sol`, requested effort `max`.

## Read the screen

Pair 001–445 means 89 tasks × 5 repetitions. Each pair contains GEODE on the
left and native Codex on the right: 890 intended cells. A cell is one task,
repetition and arm. Original cell IDs are retained, so they are not the pair
number. Play adds the next recorded tool event at the bottom; older events
move upward while arm metadata stays fixed. Use the task selector, slider,
Space, or arrow keys to navigate. Reduced-motion preferences are respected.

| Evidence shown | GEODE cells | Codex cells | Total |
|---|---:|---:|---:|
| ATIF-derived tool-event replay | 407 | 428 | 835 |
| Receipt only; no terminal reconstruction | 28 | 7 | 35 |
| Prospectively excluded; not executed | 10 | 10 | 20 |
| Intended cells | 445 | 445 | 890 |

The source contains 19,559 ATIF steps and 16,244 exactly paired tool calls and
observations. Compared with the earlier 834-cell cast index, this view adds
the preserved Codex `dna-insert` repetition 2 ATIF (cell 387,
`supplement-042-native`: 21 steps, 15 calls). Its source digest matches the
existing evidence reference. No source, attempt selection, or score changed.

## Evidence and scoring boundaries

Pairs align by task and repetition, then tool-event index, not wall time.
The arms were not necessarily executed concurrently. The video's five
events/second per arm is editorial pacing, not original terminal timing.
UTC source timestamps remain embedded; the screen displays KST. Trial wall
time includes setup, agent execution and verification.

Raw verifier reward and selected reward are different fields. The frozen
ledger assigns selected zero to canonical agent timeouts and safety refusals,
including 18 cells whose raw verifier reward is one. This view does not
re-adjudicate them. Invalid cells remain unscored. The authoritative chain is
native result/verifier receipt → frozen attempt selection → analysis; the
replay is only an observation aid.

The 20 excluded cells belong to `bn-fit-modify` and `tune-mjcf`, each five
repetitions × two arms. Their official amd64 oracle/verifier did not complete
normally through Rosetta on the arm64 host. Prospective amendments excluded
both arms before model calls. They are neither passes nor zeroes. Six other
native cells remain infrastructure-invalid. The full-suite primary remains
not measurable; this view does not claim an official leaderboard result.

All 445 pair slots are visible, but only 835 cells have reconstructable ATIF
tool-event sequences. The 35 receipt-only cells have no invented commands.
Historical parent attempts remain referenced as lineage; this is not a
separate playback of all 938 physical attempts.

## Public disclosure

The self-contained public HTML contains only tool names, allowlisted program
labels, payload sizes, hashes, timestamps, outcomes and lineage references.
Output character/line counts describe the serialized observation payload,
not necessarily stdout alone. `script` is a conservative label when no
allowlisted first program can be identified; it is not a behavioral category.
No command arguments, output bodies, model messages, provider reasoning,
credentials or machine-local absolute paths are included.

Private local HTML has bounded 16,000-character command/output excerpts and
known-pattern redaction only. It is not part of this publication and is not
approved for sharing. Source ATIF and observer-side PTY captures stay private.

`build-receipt.json` binds the data and raw-source digests; its original HTML
hashes refer to the preserved pre-CLI draft. `views-receipt.json` names the
current bottom-up HTML bytes. `browser-check.json` binds those bytes to the
445-pair, keyboard, privacy, fixed-header and bottom-scroll checks. The
publication manifest allowlists the exact distributed files. Source evidence
was read back at artifact commit
`a32abcbf78ab6100ea1e85540a2ace9436dc6f76`.

## 한국어 요약

001–445는 task와 반복 번호를 맞춘 비교 쌍입니다. 각 쌍의 왼쪽은 GEODE,
오른쪽은 Codex이며, 전체 계획은 890개 cell입니다. 재생하면 새 tool event가
아래에 나타나고 이전 기록이 위로 올라갑니다. 상단의 arm 정보는 고정됩니다.

835개 cell은 보존된 ATIF로 순서를 재구성했습니다. 35개는 결과 receipt만
남아 있어 실행 내용을 복원하지 않았고, 20개는 실행 전에 양쪽 arm에서
제외했습니다. 전체 화면을 탐색할 수 있다는 뜻이지, 모든 실행의 원본 PTY가
복구됐다는 뜻은 아닙니다. 원본 시각은 UTC로 보존하고 화면에는 KST를
표시합니다. 공개판은 tool-event 메타데이터만 담습니다.
