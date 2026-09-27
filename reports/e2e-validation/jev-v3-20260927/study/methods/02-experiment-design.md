> Historical method/decision record; current findings and corrections are in the package index. Personal paths and account identifiers have been withheld.

# Jev 잔여 실험 설계 리뷰 v3: 환경부터 게시까지

2026-09-26 · 실험 설계 리뷰어 · 읽기 전용 검토(저장소 변경·모델 호출 없음)

후속 설계: [05 사전 등록 v1 §3.5](05-preregistration.md#35-반복-신뢰도-보조-분석v1)과 [06 신뢰도 렌즈](06-reliability-lens.md)가 pass@n/pass^n·후보 폭·수정 깊이의 최신 정의를 소유한다. 아래 코드 상태는 작성 당시의 역사적 스냅샷이다. 이 보강으로 실행 횟수나 재개 권한은 바뀌지 않는다.

기준: `origin/develop` **48ada6b**, Jev 브랜치 `codex/jev-primitives-20260925` **d5d82ca**(develop 대비 3 ahead / 137 behind). `경로:행`은 develop, `(br)`은 d5d82ca 기준이다. 토큰 수치는 M4 r2·M6 r3 receipt에서 온 추정치다. 달러 수치는 저장소 가격표(`core/llm/model_pricing.toml`, 2026-09-24 갱신) 기반 참조값이며 청구액이 아니다.

## 1. 판정과 사용자 결정

**판정: 설계 방향은 유지하되, 현재 코드로는 유료 호출을 트리거할 수 없다(NO-GO).** 막는 것은 모델이 아니라 Phase 0 공백 다섯 가지다(§4 B1–B5): develop 미통합, LLM 확률 출력(V1) 부재, JJ 규모 패널·oracle 부재, 보정·클러스터 부트스트랩 코드 부재, Score 하네스 부재. 모델 없는 작업은 지금 시작할 수 있다.

**모델(사용자 결정 완료).** root, repair, LLM 비교군 모두 GPT-6 Astra / xhigh / Codex 구독(교체 계정)이다. 코드의 Astra 고정점(7개 파일 20여 곳, §4 R8)을 그대로 쓰고 M4/M6 비교 가능성도 유지된다. 조건: ① 계정 교체를 run-spec `environment`에 식별자 없이 기록, ② admission 첫 호출에서 `response_model=gpt-6-astra`·effort 수락·어댑터 해석 확인, ③ 지연은 같은 계정·같은 창 안에서만 비교. 참고로 Opus 5.5 구독 경로는 GEODE가 거부한다(`core/llm/model_catalog.py:134-139`).

**남은 결정**
1. **V1 채택**: Astra가 `{verdict, probabilities}`를 반환하고, Noul에서는 조건별 확률을 반환한다. 권고는 채택이다. 채택하지 않으면 보정과 cascade를 비교할 수 없다.
2. **Cascade**: M7에서는 두 엔진 출력으로 오프라인 계산한다(추가 호출 0). M8 live arm C는 M7에서 허용 τ가 나올 때만 승인하기를 권고한다(약 +100 호출, 코드 필요, B6).
3. **규모와 상한**: 패널 400 상태, E2E 약 120 롤아웃, 창당 Astra 약 1,200 호출, Jev 상한 $1.
4. **held-out 저작자**: test split(클러스터의 60%)을 설계자가 아닌 제2 저작자가 쓰고, 동결 전까지 `withheld-sealed`로 봉인한다.
5. **패널 전송 오류 규칙**: 현 계약은 "provider 오류가 한 번이라도 기록되면 진단 중단"이다(`docs/eval/typesafe-decision-handoff.md:152-153`). 권고: 판정 수준 패널에 한해, 응답 없는 전송 실패는 무효로 보존하고 같은 입력을 1회 대체하며 대체율이 2%를 넘으면 중단한다고 사전 등록한다. E2E는 현행 유지.
6. **live 고정 커밋**: 계획은 main 고정이고(`jev-update-plan.md:510-511`), 이번 요청은 develop 기준이다. 둘 중 하나로 확정해야 한다.

## 2. 실험 카드

**공통 규칙(아래 모든 카드에 적용)**
- **유효성.** JJ의 규칙(스키마, 라벨 소속, 유한 확률, 합 허용오차 0.025, verdict=argmax)에 현 admission 검사(`evals/benchmarks/decision_verification.py:251-266`: route·model·stop_reason·도구 없음·거부 없음)를 더한다.
- **무효의 두 종류.**
  - 판정 출력 무효는 유효 attempt의 오답이다. 정확도 분모에는 남기고 확률 지표에서는 뺀다.
  - 인프라 무효(응답 없음, 캡처 누락, 시간 초과)는 `invalid` → `unknown`이다(`docs/eval/schemas/attempt.schema.json:118-121`).
- **지표.** 정확도(무효=오답), macro-F1, Brier, NLL(하한 1e-6), 10-bin ECE, 오류 탐지 AUROC(점수 1−q), risk–coverage, source-cluster 부트스트랩 2,000회 쌍대 95% 구간. q는 최대 라벨 확률이다(Jev `confidence`는 3지선다에서 (3·max−1)/2인 분산 기반 값이라 따로 기록). 온도와 τ는 selection split에서만 적합한다.
- **동결 대상.** source commit, runner·지표 코드 해시, 질문·스키마·프롬프트 digest, 상태·풀·fixture 해시, split manifest, 봉인된 gold, τ·온도 grid, `llm_max_retries=1`, 동시성·pacing, 호출 상한, Replay 쌍.
- **판정 매핑.** 성공은 `hypothesis_status=supported`, 실패는 `not-supported`, 불명은 `mixed`, 인프라 무효는 `invalidated`와 `not-measurable`로 적는다. 모든 카드는 `outcome=diagnostic-only`, `promotion_authority=none`이다.
- **공통 중단 조건.** route·model·effort 불일치, 비밀정보 노출, 호출 상한 도달, 진행 중 사용률 90% 도달.

**C1. Choice: 완료 판정 패널(M7-V)**

| 항목 | 설계 |
|---|---|
| 가설 | 증거 기반 완료 판정에서 Jev 정확도가 Astra 대비 −5pt 이내이고, q가 오답을 구별한다(AUROC>0.5) |
| 고정 입력 | 공통 항목 + `_QUESTIONS` digest, V1 스키마 |
| arm | A Astra(V1), B Jev 1.13.0, C cascade(τ, 오프라인). 첫 단계 출력이 무효면 항상 fallback으로 넘긴다 |
| 소비자 | `MatchedVerifierAdapter` → `passed/score/reflection` → 기존 최종 verifier(운영 `verify.py` 경로는 F1) |
| oracle | 구조화된 후보 주장 × 관측 × 계약에서 규칙으로 (c, m)을 계산하고 contradicted / insufficient / supported로 옮긴다. 두 엔진이 모두 oracle과 다를 때만 제2 검토자가 판정하며, 변경 로그를 남긴다 |
| 표본 | 400 상태, source cluster ≥40개(클러스터당 ≤10), (c,m) 네 칸 균형, 호출 전 40/60 split, 상태당 엔진별 1회. 이 중 약 10%인 봉투 밖 층(스타일 적대, 유도 검증, 무참조 문장 M2)은 headline에서 빼고 따로 보고한다. 안정성: test 24 상태 × {동일 반복 2, 기준 순서 역전 1, 바꿔쓰기 1}. 지연 패널: 120 결정(고정 worker, pacing, heartbeat, 한 세션) |
| 1차 지표 | 쌍대 정확도 차 (B−A)/N_test. 구간 폭은 약 ±4–6pt 예상 |
| 판정 | 성공: 구간 하한 > −5pt 그리고 AUROC 하한 > 0.5. 실패: 구간 상한 < −5pt. 그 외는 불명. cascade: selection에서 fallback 대비 −2pt 이내이면서 coverage가 최대인 τ가 test에서도 −2pt 이내면 성공. 허용 τ가 없으면 "cascade 없음"으로 보고한다 |
| 중단 | admission 무효율이 10%를 넘으면 계약을 고치고 새 lineage로 시작한다 |

**C2. Choice: 완료 판정 E2E(M8)**

| 항목 | 설계 |
|---|---|
| 가설 | 판정 엔진 교체가 독립 oracle 기준의 task 성공, 거짓 완료, 복구, 단계별 부담을 바꾼다 |
| arm | A Astra, B Jev, (C cascade, 결정 2). 모두 `a0` inbox이며 root, 반성, 수리는 Astra xhigh |
| 고정 입력·oracle | 공통 항목 + task·주입 fixture 해시, Replay 쌍 사전 선택(M8-N 첫 task rep0, A 왼쪽·B 오른쪽). oracle은 task 소유 독립 Harbor verifier(모델 없음) |
| 표본 | M8-N: 자연 12 task × 2 rep × A/B = 48 롤아웃(C를 넣으면 +24). M8-I: C4 fixture를 쓰는 Choice arm 36 롤아웃(1 rep). task는 test-split 클러스터에서 뽑는다(τ 적합 표본 밖) |
| 소비자 | 판정 → reflection hint → root replan → 최종 후보 → oracle |
| 지표 | strict 성공 차, 거짓 완료·거짓 거부, 복구(부정 판정 → 소비 → 수정 → oracle 통과), 목적별 호출·토큰·시간(cognitive 포함). 판정 지연은 보조 지표이며 지연 주장의 근거는 C1 지연 패널이다 |
| 판정 | 클러스터가 10개 미만이면 기술통계만 쓰고 구간은 내지 않는다. 천장 규칙: admission에서 두 arm이 모두 90% 이상 통과하면 M8-N은 부담 측정으로만 보고한다 |
| 유효성·중단 | 첫 인프라 무효 셀에서 dispatch를 멈추고, 의미적 실패는 계속한다(현행). run-spec 하나당 롤아웃을 36개 이하로 나눠 무효 한 건이 미치는 범위를 줄인다 |

**C3. Choice: intent+target(패널 + Harbor 2+6)**

| 항목 | 설계 |
|---|---|
| 가설 | Jev helper가 Astra helper와 비슷한 정확도를 내면서 root 소비와 검증된 완료를 유지한다 |
| arm | A Astra typed helper, B Jev helper(`DecisionHandoffTool`). 최종 판정은 양쪽 모두 Astra |
| 고정 입력 | 공통 항목 + fixture를 재사용한다. 준비된 runner의 옛 source pin은 다시 동결한다(`.geode/eval-runs/jev-intent-harbor-20260924/protocol.md:3`) |
| 표본 | I-패널: 항목 ≥200개, inbox 가족 ≥40개. 언어, 후보 수, no-match로 층화한다(Laya 교훈). Harbor: admission 2셀 + 자연 6셀(3 inbox × 2 arm, 1 rep) |
| 소비자 | `analyze_request` → 그 tool-call ID를 소비하는 root 요청 → lookup, clarify, unsupported → oracle |
| 지표 | 패널: intent, target, joint 정확도와 Jev 보정. Astra는 helper V1(F3) 전까지 정확도만 본다. Harbor: strict 성공 차 /3, 잘못되거나 추가된 lookup, 거짓 완료, helper 교정, 호출·토큰 |
| oracle·중단 | fixture gold(`expected_intent/order/answer`, `validate_inbox_case`)와 기존 inbox oracle. 준비된 규칙대로 admission 2셀 통과와 Replay 재생 확인 전에는 자연 셀을 동결하지 않고, 첫 무효 셀에서 멈춘다 |
| 판정 | 정확도 주장은 패널에서만 한다(δ=5pt). Harbor 6셀은 소비 경로와 부담을 보는 진단이다. 분모가 3이라 구간은 내지 않는다 |

**C4. Noul: 두 조건 2×2(M7-N + M8-I)**

| 항목 | 설계 |
|---|---|
| 가설 | 모순과 근거 부족을 독립적으로 판정하면, 둘 다 참인 상태에서 두 수리 요구가 함께 전달되고 해결된다. Jev Noul의 조건별 정확도는 Astra 대비 −5pt 이내다 |
| arm | 판정 수준: C1과 같은 400 상태에 Noul 질문을 더해 Astra(V1 조건 확률)와 Jev P(true)를 비교하고, Choice와도 쌍대 비교한다. E2E: 엔진{Astra, Jev} × primitive{Choice, Noul}, 칸 (1,0)(0,1)(1,1) × 6 task = 72 롤아웃. 이 중 Choice 36개는 C2와 공유한다 |
| 소비자 | `primitive=noul` → 불리언 투영(Jev p≥0.5) → 우선순위 verdict → Astra 수리. (1,1)에서는 두 hint를 합친다((br) `decision_verification.py:337,342-348,362-372`) |
| oracle | C1과 같은 규칙이다. 주입은 기존 intervention만 쓴다. (1,0)은 관측 후 모순, (0,1)은 관측 전 조기 주장, (1,1)은 한 후보 안의 계약 위반 쓰기 주장과 미관측 상태 주장이다(trial당 개입 1회) |
| 지표 | 조건별 정확도, Brier, ECE, AUROC. 1차 지표는 두 조건 joint 정확도의 쌍대 차다. (1,1)에서 두 조건을 모두 표시한 비율. E2E: (1,1)에서 수리 1회로 완전 복구한 비율, 수리 라운드 수, 추가 호출 |
| 고정 입력·중단 | 공통 항목 + `_NOUL_QUESTIONS` digest, 주입 fixture 해시, Replay 쌍((1,1) 첫 task, Astra-Noul 왼쪽·Jev-Noul 오른쪽). 중단은 패널이면 C1, E2E면 C2와 같다 |
| 판정·유효성 | 공통 규칙을 따른다. 판정 기준은 C1과 같다(δ=5pt). 임계 0.5가 1차 규칙이고, selection에서 적합한 임계는 보조로만 쓴다. E2E는 기술통계로만 보고한다. 질문을 둘로 나눴다고 통계적 독립이 되지는 않는다 |

**C5. Score: best_of 후보 선택(Score-S)**

| 항목 | 설계 |
|---|---|
| 가설 | 같은 동결 풀에서 Jev 점수의 argmax가 Astra 점수의 argmax 대비 oracle-best 선택률 −10pt 이내다 |
| 풀·고정 입력 | S-통제: C1 상태로 만든 80개 풀(클러스터당 2개, 후보 4개, 근거를 후보 본문에 포함, 2,000자 이하). S-자연: 12 task에 `delegate_task(best_of=4)`를 **한 번** 실행해 read-only 풀을 해시로 동결한다. 풀·순서당 selector 1회 |
| oracle·유효성 | 선택 전에 모델 없이 후보 등급을 매긴다. S-통제는 (c,m)에서(supported 3, 근거 부족 2, 모순·둘 다 0), S-자연은 기존 inbox oracle의 항목 정답 수에서. 유효성은 공통 규칙 + R1의 Score 기대값 허용오차 |
| arm | Astra 점수(pointwise), Jev Score, 운영 listwise `select_candidate`(참조용, 예산이 모자라면 가장 먼저 뺀다). 기준선: 첫 후보(운영 fallback)와 무작위 |
| 순서 | 정순과 역순을 모두 실행하고 두 점수의 평균으로 고른다. 동률은 사전 등록한 해시 규칙으로 가르며, 입력 순서를 쓰지 않는다 |
| 소비자 | `_select_best_candidate`(`core/agent/tool_executor/executor.py:2051-2113`) → `candidate_judge` 미들웨어 → winner. root 하류 소비는 F2에서 다룬다 |
| 지표 | oracle-best 선택률(무효와 fallback은 오답), regret, pass@1·oracle@4·selected·gap-closed(CLM 교훈), 순서 일관성, 후보 순위 상관 |
| 판정·중단 | 통제 풀 구간 하한 > −10pt면 성공, 상한 < −10pt면 실패, 그 외 불명. 자연 풀은 비변별 풀 비율을 먼저 제시하고 기술통계로만 보고한다(admission 비변별률 >70%면 서술용) |

**C6. 실패 처리: 계약 적합성 감사**
- 가설: 실제로 발생한 무효 판정, 전송 실패, fallback은 하나도 선택·완료 성공으로 세어지지 않고, 완료된 호출의 usage는 남거나 unknown으로 표시된다.
- 소비자: 타입 검증 → 선택 거부(`judge_error` 후 첫 후보 fallback) 또는 전달 보류(`verification_error`) → 호출 원장.
- 방법·지표: 모든 run의 receipt를 전수 대조해 적합률(적합 사건/전체 사건)을 낸다. 거부 경로, usage, 성공 분모 제외를 확인하며 새 호출은 없다.
- 판정: live 사례 1건 이상이 모두 적합하면 성공. 부적합이 1건이라도 있으면 실패이며, 해당 증거를 무효화하고 superseded lineage로 남긴다. live 사례가 0건이면 불명이고, 오프라인 회귀 라벨로만 설명한다.

## 3. 실행 순서와 quota 계획

1. **통합(모델 없음).** develop을 토픽에 merge(rebase 금지) → 생성 문서 재생성 → V1, 허용오차, 지표 모듈, 패널 builder·oracle, Score-S 하네스, (결정 2 승인 시) arm C 구현 → 전체 CI → PR → 커밋 고정.
2. **모델 없는 증명.** oracle 자기검사(gold 재계산 100% 일치, 판정 기록), 합성 데이터로 지표·부트스트랩·cascade 시뮬레이터 검증, 모의 selector로 Score 하네스 검증, Harbor `--infra-preflight`(24시간 유효), 합성 trajectory로 `stage_trajectory_release`·`validate-publication` 예행.
3. **소규모 admission(U0).** 카드마다 최소 셀만 돌린다. 무효율, 허용오차 분류, 경로, Replay 재생을 확인한 뒤에만 넘어간다.
4. **승인된 run.** M7 selection → τ·온도 동결 → M7 test·안정성·지연 → Score → intent → M8-N → M8-I.
5. **감사, 정제, 게시.** receipt에서 지표 재계산 → 무효 행을 보존한 파생 표 → E2E는 `geode.trajectory@1`(scope-complete, 본문 비공개면 replay-incomplete 명시), 패널은 component 판정이라 디렉터리·분모 분리 → 개인정보 검토 → `validate-publication` → artifact PR → 정확한 커밋 read-back → GEODE 원장 기록.

**Quota 계획.** OpenAI는 구독 토큰 한도를 공개하지 않으므로 사용량을 호출 수와 토큰 수로 표현한다. 호출당 기준(M4 r2·M6 r3 실측): Astra 판정 입력 약 3.5K/출력 0.1K, 자연 롤아웃 Astra 4.5회·입력 12K/출력 1.2K, 주입 롤아웃 약 1.1배, Jev 판정 입력 약 2.6K.

| 단위 | Astra 호출 | Astra 입력/출력 토큰 | Jev 호출 | 창 |
|---|---:|---:|---:|---|
| U0 admission | ≈90 | 0.3M / 0.03M | ≈45 | W1 |
| U1 M7 selection | 320 | 1.2M / 0.05M | 320 | W1 |
| U2 M7 test+안정성 | 672 | 2.4M / 0.09M | 672 | W1 |
| U3 지연 패널 | 120 | 0.4M / 0.02M | 120 | W1 |
| U4 Score 통제 | 320 | 1.0M / 0.05M | 160 | W2 |
| U5 Score 자연(생성 포함) | ≈240 | 0.75M / 0.07M | 24 | W2 |
| U6 intent 패널+Harbor 6셀 | ≈70 | 0.3M / 0.02M | ≈45 | W2 |
| U7 M8-N(A/B) | ≈205 | 0.55M / 0.06M | ≈30 | W2 |
| U8 M8-I(72) | ≈400 | 1.0M / 0.09M | ≈70 | W2 |
| 합계 | ≈2,440 (C 추가 시 약 +100) | ≈7.9M / ≈0.5M | ≈1,490 | |

Jev 비용은 입력 약 4M 토큰 × $0.042/M ≈ $0.17이다(출력 무료). Astra는 구독이라 추가 청구가 없다. 가격표로 환산한 API 참조값은 약 $100이지만 비용 주장에는 쓰지 않는다.

창 분할 규칙:
- G0에서 계정의 사용률 표시와 초기화 시각을 기록하고, U0 뒤 "100 호출당·입력 1M 토큰당 사용률 증가"를 실측해 이후 단위를 투영한다.
- 투영 사용량이 남은 여유의 80%를 넘는 단위는 다음 창으로 미룬다. 단위는 창 경계를 넘지 않는다(U1과 U2는 별개 단위).
- 단위 도중 한도가 소진되면 인프라 무효다. 제자리 재개 없이 다음 창에서 새 lineage로 시작한다.
- 정확도 단위는 동시성 4 이하, 지연 단위는 고정 worker·pacing으로 한 세션. 실행 중 같은 계정의 다른 작업 금지(큐잉이 지연을 오염).
- 기본안: W1 약 1,200 호출(판정 패널), W2 약 1,235 호출(Score, intent, E2E). U0 실측상 여유가 부족하면 U8을 W3로 넘긴다.

## 4. 이격 분류

**BLOCKING**
- **B1 통합.** primitive 코드는 로컬 d5d82ca에만 있다. develop의 파서는 Choice 전용이다(`core/llm/adapters/typesafe.py:126-145`).
- **B2 V1 부재.** LLM 판정은 라벨만 낸다(`evals/benchmarks/decision_verification.py:96-98`). 투영은 이진이다(`:274-277`). Noul의 LLM arm은 불리언만 낸다((br) `:141-144`). checker(`scripts/eval/check_harbor_observations.py`)도 함께 바꿔야 한다.
- **B3 패널과 oracle 부재.** M5는 task 하나에서 나온 종속 상태 3개이고, M4는 inbox 3개다. fixture 검증에는 `validate_inbox_case`(`evals/benchmarks/decision_handoff_runtime.py:117-169`)를 재사용할 수 있다.
- **B4 지표 코드 부재.** Brier, NLL, ECE, AUROC, risk–coverage, 클러스터 부트스트랩이 모두 없다. 재사용할 수 있는 것은 task 델타 부트스트랩(`evolve/crucible/promotion.py:30-69`)뿐이다.
- **B5 Score 하네스 부재.** 어댑터는 동결 풀과 정확히 같은 judge 프롬프트만 가로챈다((br) `evals/benchmarks/decision_candidate.py:111-122`). 풀 생성·주입, oracle, Replay가 없다((br) `docs/eval/typesafe-decision-handoff.md:72-78`, `jev-update-plan.md:411`).
- **B6 live cascade(결정 2가 승인되면).** 엔진 값은 `llm|jev`뿐이다(`evals/platforms/harbor_handoff.py:90`). checker는 판정 하나에 호출 하나를 전제한다.

**REQUIRED-BEFORE-TRIGGER**
- **R1 허용오차.** 확률 합 허용오차가 1e-5다(`core/llm/adapters/typesafe.py:140`; (br) `:216-218`). Score 기대값도 1e-5다((br) `:220-231`). 공식 문서는 반올림 정밀도를 보장하지 않는다. 합은 0.025로 두고, Score 기대값 허용오차는 admission 실측 반올림 폭으로 동결하며, 엄격·완화 분류를 둘 다 기록한다.
- **R2 무효 매핑.** 선택된 무효 attempt는 not-measurable이 된다(`scripts/eval/contract.py:692-697,755-762`). JJ의 "무효=오답"과 이 규칙을 `invalidation_rule`에 구분해 적고 결정 5를 반영한다.
- **R3 예산.** r2 run-spec은 `limit=null, unit=uncapped`였고, intent 프로토콜도 상한이 없다(`.geode/eval-runs/jev-intent-harbor-20260924/protocol.md:40`). 단위별 호출 상한과 Jev USD 상한을 적는다.
- **R4 순서와 동률.** 입력 순서로 가르는 동률 규칙((br) `decision_candidate.py:247`)과 index 0 fallback(`core/agent/candidate_sampling.py:241-263`)은 둘 다 앞쪽 후보에 유리하게 기운다. 양순서 실행과 해시 동률 규칙으로 바꾼다.
- **R5 q와 임계.** q=최대 확률로 사전 등록한다. Noul 0.5 고정((br) `decision_verification.py:337`)을 1차 규칙으로 두고, 적합 임계는 보조로 쓴다. τ·온도 grid도 사전 등록한다.
- **R6 Noul 주입.** intervention은 before/after 두 종류이고 trial당 1회다(`decision_handoff_runtime.py:184-203`). (1,1) 구성 규칙과 oracle 규칙을 fixture로 동결한다.
- **R7 지표 증거.** 1차 지표는 native-result의 분자와 분모에서 와야 한다(`contract.py:231-235,764-784`). 등록된 measurement 스키마는 geo-vector 하나뿐이다(`:29,379-382`). 그래서 보정 지표는 보조 지표로 둔다.
- **R8 고정점.** Astra 고정(`decision_handoff.py:33,197-205`, `decision_handoff_runtime.py:22,473`, `decision_verification.py:139-146,164-167`, `harbor_handoff.py:86-96`(180초 포함), `check_harbor_observations.py:814-823`, (br) `decision_candidate.py:63-65,116-122`)은 유지한다. live pin(결정 6), `llm_max_retries=1`((br) 문서 `:80`), intent runner 재동결도 여기서 처리한다.
- **R9 계정 교체.** 기록하고 권한을 확인한다(§1).
- **R10 Score 변별력.** M4에서 Astra는 72/72 항목을 맞혔다. 자연 풀에서는 후보가 대부분 동급일 가능성이 크다. 통제 풀 사용과 비변별률 보고를 사전 등록한다.

**FOLLOW-UP**
- **F1 운영 경로 동등성.** 운영 Jev 판정은 요청을 4,000자, 후보를 2,000자로 자르고, 상태와 질문의 모양도 다르다(`core/agent/verify.py:848-852`). 결과도 이진이다(`:892,900`). 따라서 eval 결과를 운영 옵션으로 옮기지 않는다.
- **F2 Score-E.** 동결 풀을 `delegate_task` 결과에 주입해 root 하류 소비와 Replay를 측정한다(`executor.py:1948-1953`).
- **F3 intent helper V1.** Astra helper는 라벨만 낸다(`evals/benchmarks/decision_handoff.py:218-229`). intent cascade도 여기서 다룬다.
- **F4 새 cohort 정규화기.** #45는 전용 정규화를 썼고, Terminal-Bench projector는 범용이 아니다(`docs/eval/external-artifact-repository.md:320-322`). 또 `validate-publication`은 GEODE 원장 파일을 요구한다(`contract.py:1005-1007`).
- **F5 비용 대응 비교군(Astra 저 effort).** 고정 xhigh 규칙 때문에 이번 범위 밖이다.

## 5. 위험과 과대주장 금지

**위험.** 패널 저작량(클러스터 40개 이상, 제2 저작자)이 일정의 병목이다. Score 반올림으로 Jev 무효가 체계적으로 생길 수 있다. 자연 E2E가 천장에 붙을 수 있다. 계정 사용률 투영에 오차가 있다. 180초 한도 안에서 수리 라운드가 시간 초과될 수 있다.

**금지 규칙**
1. eval 어댑터 결과를 운영 `judgment_engine=jev`의 성능으로 쓰지 않는다.
2. 확률은 권한이 아니다. Score는 위치이지 confidence가 아니다. Noul의 p는 측정하기 전까지 보정값이 아니다.
3. 구간은 클러스터 40개 이상인 패널에서만 낸다. E2E와 intent Harbor는 기술통계로만 보고한다.
4. 지연 주장은 C1 지연 패널에서만 한다. E2E 전체 시간에는 root와 cognitive 변동이 섞여 있다.
5. 구독 API 환산액, Jev 요율 계산액, 실청구액을 한 숫자로 합치지 않는다. usage 누락은 unknown이며, 보수적 예약액은 별도 열에 둔다.
6. 옛 cohort(M4–M6, r6)와 합산하지 않는다. 교체 계정의 지연을 M4 시점과 비교하지 않는다.
7. τ, 온도, 임계는 selection에서만 적합한다. test를 본 뒤에는 다시 적합하지 않는다.
8. Replay 쌍은 결과가 나오기 전에 고정하고, 실패하더라도 교체하지 않는다. fallback은 Jev 성공이 아니다.
9. JJ, CLM, Laya의 수치를 GEODE 결과로 옮기지 않는다. 결정을 바꾼 교훈만 반영한다: JJ(무효=오답, 합 허용오차 0.025, 양순서, selection 기반 τ, 클러스터 부트스트랩), CLM(pass@1·oracle@N·selected 동시 보고), Laya(같은 사례에서 Choice와 다중 Noul 비교, 언어·no-match 층화, 다중 검토자 부재 한계).
