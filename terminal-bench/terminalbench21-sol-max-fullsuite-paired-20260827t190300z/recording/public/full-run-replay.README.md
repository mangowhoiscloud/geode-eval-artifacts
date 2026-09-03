# Full-run replay / 전체 런 재생

## 한국어

- 범위: 동결된 890개 의도 셀 전체입니다.
- `834`개는 선택된 ATIF에서 만든 로컬 상세 replay가 있습니다.
- `36`개는 ATIF가 없어 result/verifier/attempt receipt 사건 카드로 재생합니다.
- `20`개는 사전 대칭 제외되어 실행되지 않았습니다.
- `full-run-overview.cast`는 공개 가능한 890-cell 상태 개요이며 원본 PTY가 아닙니다.
- 로컬 상세 재생: `python3 replay-full-run.py --cell 1 --detail`
- 전체 빠른 재생: `python3 replay-full-run.py --all --detail --speed 100`

## English

- Scope: all 890 intended cells in the frozen design.
- `834` cells have local detailed replays derived from selected ATIF trajectories.
- `36` cells lack selected ATIF and replay as result/verifier/attempt receipt events.
- `20` cells were prospectively excluded symmetrically and were never executed.
- `full-run-overview.cast` is a public 890-cell status overview, not a raw PTY recording.
- Local detail: `python3 replay-full-run.py --cell 1 --detail`
- Fast full replay: `python3 replay-full-run.py --all --detail --speed 100`

Score authority remains Harbor `result.json` plus verifier receipts. Replays explain procedure and behavior only.
