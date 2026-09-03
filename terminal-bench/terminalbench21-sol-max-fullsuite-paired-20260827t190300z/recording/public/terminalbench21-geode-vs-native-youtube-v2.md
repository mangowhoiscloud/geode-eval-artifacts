# YouTube upload metadata / 업로드 메타데이터

## Title

GEODE vs Native Codex — Terminal-Bench 2.1 Evidence | 한국어 + English

## Description

한국어 설명 뒤에 영어 설명이 이어집니다. 같은 `gpt-5.6-sol` 모델을 GEODE와 native Codex harness에서 비교한 로컬 paired-runtime 증거입니다. 점수 권위는 Harbor result와 verifier receipt이며, 화면·ATIF 파생 replay는 절차와 행동 설명용입니다. 445-cell/arm primary는 측정 불가이므로 공식 leaderboard 순위와 동등하게 해석할 수 없습니다.

Korean is followed by English. This is local paired-runtime evidence comparing GEODE and native Codex with the same `gpt-5.6-sol` model. Harbor results and verifier receipts are the scoring authority; screen records and ATIF-derived replays explain procedure and behavior. The 445-cell-per-arm primary is not measurable and is not rank-equivalent to the official leaderboard.

## Chapters

0:00 한국어 · 개요와 데이터 분류
0:21 SUITE MAP — Terminal-Bench 2.1은 실제 터미널 작업 묶음입니다
0:37 STORAGE — 저장 루트는 하나, 권위는 층별로 분리
0:52 EXECUTION — 한 trial은 새 컨테이너에서 시작합니다
1:06 HARBOR MODEL — Harbor는 trial 틀을, agent는 기록 방식을 소유합니다
1:20 RUN FLOW — 실행 전: 조건을 먼저 얼립니다
1:50 ACCUMULATION — artifact는 trial에서 시작해 ledger로 모입니다
2:05 TRAJECTORY — trajectory는 행동 기록, 점수표가 아닙니다
2:19 EVIDENCE — 점수와 화면 기록은 끝까지 분리합니다
2:30 REPLAY COVERAGE — 관찰 범위는 동결된 890개 셀 전체를 덮습니다
2:43 FAILURE SCHEMA — 실패 판정은 한 스키마로 연결됩니다
2:56 FAILURE PATTERNS — 실패는 네 가지 패턴으로 갈렸습니다
3:10 FAILURE TRACE — trajectory를 보면 같은 0점도 모양이 다릅니다
3:25 DESIGN — 비교 설계: 같은 모델, 다른 harness
3:38 TASK LEDGER — 선택된 셀을 task별로 다시 셉니다
4:03 OBSERVER INDEX — 관찰자 기록 67개를 빠짐없이 인덱싱
4:27 PROCEDURE EVIDENCE — 실제 실행 화면은 이렇게 복원됩니다
4:48 PRIMARY — 20개 셀은 두 task의 환경 실행 불가로 제외
5:06 RESULT — 대신, 관측 가능한 분모를 그대로 제시
5:19 PAIRED CELLS — 같은 429개 셀에서 어디가 갈렸는가
5:30 PUBLICATION — 공개는 allowlist 복사 후 원격에서 다시 검증
5:43 BOUNDARY — 결론: 재현 가능한 secondary evidence
5:56 English · Overview and data classification
6:17 SUITE MAP — Terminal-Bench 2.1 is a suite of real terminal tasks
6:33 STORAGE — One storage root, authority separated by layer
6:48 EXECUTION — Every trial starts in a fresh container
7:02 HARBOR MODEL — Harbor owns the trial envelope; each agent owns its capture method
7:16 RUN FLOW — Before execution: freeze conditions
7:46 ACCUMULATION — Artifacts flow from each trial into one ledger
8:01 TRAJECTORY — A trajectory is a behavior trace, not a scorecard
8:15 EVIDENCE — Scores and screen records remain separate
8:26 REPLAY COVERAGE — Observation coverage spans all 890 frozen cells
8:39 FAILURE SCHEMA — One schema connects every failure decision
8:52 FAILURE PATTERNS — Failures separated into four patterns
9:06 FAILURE TRACE — Trajectories reveal different shapes behind the same zero
9:21 DESIGN — Comparison design: same model, different harness
9:34 TASK LEDGER — Recount selected cells by task
9:59 OBSERVER INDEX — All 67 observer records are indexed
10:23 PROCEDURE EVIDENCE — This is how the execution view is recovered
10:44 PRIMARY — 20 cells were excluded because two tasks could not run in this environment
11:02 RESULT — Report the observable denominator instead
11:15 PAIRED CELLS — Where did the same 429 cells diverge?
11:26 PUBLICATION — Publication copies an allowlist, then verifies the remote bytes
11:39 BOUNDARY — Conclusion: reproducible secondary evidence
