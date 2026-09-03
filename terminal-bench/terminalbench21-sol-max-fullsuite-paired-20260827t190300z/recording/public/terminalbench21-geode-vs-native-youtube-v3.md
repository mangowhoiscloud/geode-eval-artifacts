# YouTube upload metadata / 업로드 메타데이터

## Title

GEODE vs Native Codex — Terminal-Bench 2.1 Evidence | 한국어 + English

## Description

한국어 설명 뒤에 영어 설명이 이어집니다. 같은 `gpt-5.6-sol` 모델을 GEODE와 native Codex harness에서 비교한 로컬 paired-runtime 증거입니다. 점수 권위는 Harbor result와 verifier receipt이며, 화면·ATIF 파생 replay는 절차와 행동 설명용입니다. 445-cell/arm primary는 측정 불가이므로 공식 leaderboard 순위와 동등하게 해석할 수 없습니다.

Korean is followed by English. This is local paired-runtime evidence comparing GEODE and native Codex with the same `gpt-5.6-sol` model. Harbor results and verifier receipts are the scoring authority; screen records and ATIF-derived replays explain procedure and behavior. The 445-cell-per-arm primary is not measurable and is not rank-equivalent to the official leaderboard.

## Chapters

0:00 한국어 · 개요와 데이터 분류
0:08 CONTENTS — 먼저 다섯 가지 핵심 메시지를 공개합니다
0:22 WHY THIS EVAL — 왜 같은 모델을 두 harness에서 다시 측정했는가
0:48 SUITE MAP — Terminal-Bench 2.1은 실제 터미널 작업 묶음입니다
1:04 MEASUREMENT UNITS — 숫자를 읽기 전에 측정 단위를 고정합니다
1:19 STORAGE — 저장 루트는 하나, 권위는 층별로 분리
1:34 EXECUTION — 한 trial은 새 컨테이너에서 시작합니다
1:48 HARBOR MODEL — Harbor는 trial 틀을, agent는 기록 방식을 소유합니다
2:02 RUN FLOW — 실행 전: 조건을 먼저 얼립니다
2:32 ACCUMULATION — artifact는 trial에서 시작해 ledger로 모입니다
2:47 TRAJECTORY — trajectory는 행동 기록, 점수표가 아닙니다
3:01 TRAJECTORY WORKFLOW — 행동 기록과 점수는 두 lane에서 정제·배포됩니다
3:16 EVIDENCE — 점수와 화면 기록은 끝까지 분리합니다
3:27 REPLAY COVERAGE — 관찰 범위는 동결된 890개 셀 전체를 덮습니다
3:40 FAILURE SCHEMA — 실패 판정은 한 스키마로 연결됩니다
3:53 FAILURE PATTERNS — 실패는 네 가지 패턴으로 갈렸습니다
4:07 FAILURE TRACE — trajectory를 보면 같은 0점도 모양이 다릅니다
4:22 DESIGN — 비교 설계: 같은 모델, 다른 harness
4:35 TASK LEDGER — 선택된 셀을 task별로 다시 셉니다
5:00 OBSERVER INDEX — 관찰자 기록 67개를 빠짐없이 인덱싱
5:24 PROCEDURE EVIDENCE — 실제 실행 화면은 이렇게 복원됩니다
5:45 PRIMARY — 20개 셀은 두 task의 환경 실행 불가로 제외
6:03 RESULT — 대신, 관측 가능한 분모를 그대로 제시
6:16 PAIRED CELLS — 같은 429개 셀에서 어디가 갈렸는가
6:27 PUBLICATION — 공개는 allowlist 복사 후 원격에서 다시 검증
6:40 BOUNDARY — 결론: 재현 가능한 secondary evidence
6:53 English · Overview and data classification
7:01 CONTENTS — Five core messages come first
7:15 WHY THIS EVAL — Why measure the same model through two harnesses?
7:41 SUITE MAP — Terminal-Bench 2.1 is a suite of real terminal tasks
7:57 MEASUREMENT UNITS — Define the measurement units before reading the numbers
8:12 STORAGE — One storage root, authority separated by layer
8:27 EXECUTION — Every trial starts in a fresh container
8:41 HARBOR MODEL — Harbor owns the trial envelope; each agent owns its capture method
8:55 RUN FLOW — Before execution: freeze conditions
9:25 ACCUMULATION — Artifacts flow from each trial into one ledger
9:40 TRAJECTORY — A trajectory is a behavior trace, not a scorecard
9:54 TRAJECTORY WORKFLOW — Behavior records and scores are refined and published in two lanes
10:09 EVIDENCE — Scores and screen records remain separate
10:20 REPLAY COVERAGE — Observation coverage spans all 890 frozen cells
10:33 FAILURE SCHEMA — One schema connects every failure decision
10:46 FAILURE PATTERNS — Failures separated into four patterns
11:00 FAILURE TRACE — Trajectories reveal different shapes behind the same zero
11:15 DESIGN — Comparison design: same model, different harness
11:28 TASK LEDGER — Recount selected cells by task
11:53 OBSERVER INDEX — All 67 observer records are indexed
12:17 PROCEDURE EVIDENCE — This is how the execution view is recovered
12:38 PRIMARY — 20 cells were excluded because two tasks could not run in this environment
12:56 RESULT — Report the observable denominator instead
13:09 PAIRED CELLS — Where did the same 429 cells diverge?
13:20 PUBLICATION — Publication copies an allowlist, then verifies the remote bytes
13:33 BOUNDARY — Conclusion: reproducible secondary evidence
