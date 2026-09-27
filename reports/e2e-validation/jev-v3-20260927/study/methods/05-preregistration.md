> Historical method/decision record; current findings and corrections are in the package index. Personal paths and account identifiers have been withheld.

# 05 · Jev v3 사전 등록 (동결 전 초안)

- 작성: 2026-09-26. v0과 v2–v2.2는 실험팀 Run 담당, v1(§3.2 Score 명칭과 §3.5)은 Codex가 썼다. 모델 호출 0회, 저장소 쓰기 0회.
- 상위 문서: [02 설계](02-experiment-design.md), [01 환경·통합](01-environment-integration.md), [03 데이터 런북](03-data-runbook.md). 명명·테이블·무효 분류는 03을 따르고, 여기서 다른 점만 따로 적는다.
- 상태: **초안(v2.2 보완 5)**. 단위별 동결은 §0의 게이트를 모두 통과한 뒤 run-spec JSON으로 한다. 동결 이후에는 이 문서가 아니라 동결된 파일이 권위를 갖는다.
  - v1은 [06 신뢰도 렌즈](06-reliability-lens.md)의 보조 지표를 더했다.
  - v2는 22:1x KST 사용자 결정을 실행 설계에 반영했다: E2E 쌍 동시 실행, 패널과 E2E 비중첩, U3 단독 슬롯, 공유 계정, quota 초기화권.
  - v2.1은 selection split과 I-패널 저작, E2E 원천 누설 검토, m 요인 누설 완화를 더했다.
  - v2.2는 조율자가 전달한 결정을 반영했다: E2E 원천 옵션 E 채택, 쌍 동시 열의 정본 이름, 통합 담당 GAP 가운데 Run 몫의 절차(§3.7), held-out 재빌드, 외부 검증 단위 X1·X2(사용자 결정, §11).
  - v2.2 보완 5는 Codex 인계 뒤 고정 #2 후보의 0028–0030 구현과 문구를 맞췄다. 고정 #2 확정·단위 동결·실행 재개는 별도 게이트다.
  - 어느 버전도 실행 재개 승인이 아니다.
- 실행 패킷: run-packets/ (역사적 참조: `run-packets/README.md`; 해당 자료는 이 공개본에 포함되지 않음). run-spec 초안, 슬롯 행렬, quota 원장, receipt 필드, U0 목록이 들어 있다.

## 0. 권한과 동결 게이트

조율자 확정 결정(2026-09-26):
- V1 채택.
- cascade는 M7에서 오프라인으로 계산하고, M8 live arm C는 §6 조건을 충족할 때만 실행한다.
- 규모: 패널 400 상태, E2E 약 120 롤아웃, 창당 Astra 약 1,200 호출, Jev $1. v2부터 "창당 1,200"은 규모를 가늠하는 표기로만 남긴다. quota는 일정 제약이 아니다(§7).
- held-out은 별도 저작 에이전트가 쓰고 봉인한다.
- 패널 전송 오류 규칙은 §4.2대로 한다.
- 고정 커밋은 필수 CI를 통과한 정확한 PR head이며, Build 담당이 확정한다. (v2.2 보완 4) 고정 커밋은 트랙별로 두 개다(§1.6): #1 `7cd052649`(E 트랙), #2 이후 head(P·G·solo).

사용자 결정(2026-09-26 22:1x KST, v2):
1. **E2E는 쌍 동시 실행한다.** 각 과제·반복의 A/B(C 승인 시 C 포함)를 같은 시간대에 동시에 시작해 같은 부하를 받게 한다. 쌍과 쌍 사이는 순차다(§2.4).
2. **판정 패널은 E2E가 돌지 않는 빈 시간에만 돌리고 E2E와 겹치지 않는다.** U3 지연 패널은 단독 슬롯이다(§2.5).
3. **계정은 로컬에 로그인된 계정이다**(fp `57faa696f3a8`, plan `prolite`). 영상 작업 Codex 세션이 같은 계정을 함께 쓴다(사용자 승인). 이 점은 한계로 명시하고, 지연은 쌍 내부 비교를 1차로 해석한다(§1.4, §3.6).
4. **G0(22:16 KST)**: 주간 창 하나(604,800초), used 51%, reset 2026-10-01 04:10 KST, 5시간 창 없음.
5. **quota는 일정 제약이 아니다**(사용자에게 초기화권이 있음). 단위를 줄이거나 미루지 않는다. 투영 사용률이 90%를 넘으면 멈추고 초기화를 요청한다(§7).

v2.2 결정(2026-09-26, 조율자 전달):
6. **E2E 원천은 옵션 E다.** 제2 저작자가 패널 밖 E2E 전용 원천 20개를 쓰고 봉인한다. 옵션 T+와 S는 기각했다(§2.3).
7. **쌍 동시 열은 조율자 목록이 정본이다.** Run 초안의 이름은 폐기 예정 별칭이다(§2.4).
8. **외부 검증 단위 X1·X2를 더한다(사용자 결정).** X1은 CUAVerifierBench로 Choice 완료 판정을, X2는 Mind2Web으로 Score 후보 선택을 본다. 외부 데이터로는 아무것도 튜닝하지 않는다(§11).

v2.2 보완 결정(2026-09-27, 조율자 전달):
9. **X2 listwise 참조를 유지한다.** U4와 같은 구성이다({Astra pointwise, listwise} + Jev, 양순서). Astra 960/1008, Jev 480.
10. **X1 admission(X1a)을 더한다.** 가장 긴 두 상태를 두 엔진이 받는지 먼저 확인하고, 통과해야 X1을 동결한다(엔진마다 2호출).
11. **X1 파생 파일은 기본이 reproducible-cache다.** ID·스크립트·해시·집계만 공개한다. 파생 텍스트 게시는 공개 단계의 개인정보 검토 뒤에 따로 정한다(§11.8).
12. **McNemar는 서술용이다.** 불일치 쌍 수 (b, c)만 보고하고 p값은 내지 않는다(§3.4의 "보조 지표는 추가 검정 없음").
13. **Score-S는 통합 패치 0024의 제한 동시 실행(≤4, 명시 인자, 산출 바이트 동일)을 쓴다.** 0024가 들어오기 전에는 run-spec의 동시성 값을 PENDING으로 둔다(§11.5).

단위를 동결하려면 아래 다섯 게이트를 모두 통과해야 한다. 하나라도 빠진 단위는 **"미실행: 선행조건 부재"**로 run-log에 남긴다. 조용히 빼지 않는다.

| 게이트 | 내용 | 제공자 |
|---|---|---|
| G-1 소스 | 필수 CI를 통과한 PR head SHA(`dirty=false`). §1.3의 기능 포함 여부를 목록으로 확인한다. (v2.2 보완 4) 단위는 자기 트랙의 고정 SHA를 쓴다(§1.6) | Build |
| G-2 입력 | 패널·풀·fixture·I-패널 해시와 split manifest. test 클러스터와 I-패널은 봉인하고 gold는 해시만 전달한다. (v2.2) E2E 원천 공개 목록(옵션 E), 외부 데이터 동결 manifest(X1·X2) | 저작 에이전트, 외부 데이터 담당 |
| G-3 무모델 증명 | oracle 재계산 100% 일치, 합성 데이터로 지표 검증, runner self-test, Harbor infra proof(당일, 24시간 유효), offline wire preflight | Build·Run |
| G-4 quota·계정 | G0 스냅샷(§7, 22:16 기록 완료)과 계정 지문 receipt(§1.2) | Run(조회는 사용자 승인 경로) |
| G-5 트리거 | 조율자가 트랙별 고정 SHA를 전달한다(사용자 지시를 함께 전달받음) | 조율자 |

변경 규칙:
- 동결 전에는 이 문서를 수정하고 변경 이력(§12)에 남긴다.
- 단위 동결 뒤에 입력·프롬프트·스키마·지표 코드를 바꾸면 그 단위는 superseded가 되고 새 lineage(`-rN`)로 다시 시작한다.
- U1이 시작된 뒤 판정 프롬프트나 스키마를 바꾸면 U1부터 새 lineage로 간다.

## 1. 공통 고정 조건

### 1.1 경로와 실행

| 항목 | 고정값 |
|---|---|
| LLM 경로 | root·reflection·final·replan·LLM arm 모두 `gpt-6-astra` / openai / **subscription** / `xhigh`. 로컬에 로그인된 Codex 계정(fp `57faa696f3a8`, plan `prolite`)의 파일 auth(`[local-path-withheld])를 쓴다 |
| Jev | `jev-1.13.0`, 직접 TypeSafe, effort `none`. 전역 `judgment_engine=llm` |
| 경로 위반 | Astra의 PAYG/API 경로, 다른 모델, effort가 xhigh가 아님, Jev 모델 불일치, 전역 Jev 활성, `response_model`·provider 불일치. 모두 invalid이며 단위를 즉시 중단한다(§4) |
| 재시도 | 패널은 호출 안 재시도 0회, runner 수준 대체만 허용(§4.2). E2E는 `llm_max_retries=1`로 동결하고, provider 오류가 기록되면(복구돼도) 중단한다(현행) |
| 동시성·제한 | 패널 동시성 ≤4. Astra 호출 180초, Jev 60초. U3는 §2.4의 쌍 동시 모드다. E2E는 쌍 동시 실행이다: 슬롯 안 arm 2개(C 포함 3개)를 동시에 띄우고 슬롯 사이는 순차다(§2.4). root 180초/6라운드, agent 210초, setup 600초, verifier 30초, watchdog 930초, cleanup 120초 |
| 소스·환경 | 트랙별 고정 SHA(§1.6)의 `git archive`, `uv.lock`, Harbor 0.22.0. Harbor venv는 `[local-path-withheld] 확정했다(Build-A가 기존 실행 7건으로 확인). 이미지 digest, verifier no-network. Docker 자원(8 CPU, 8 GB)에서 동시 trial 3개가 가능한지는 U0에서 확인한다 |
| 가격 참조 | Jev 입력 $0.042/M, 출력 $0(동결 전 재확인해 날짜·출처 기록). Astra API 환산은 참조값일 뿐 비용 주장에 쓰지 않는다 |

### 1.2 계정·비밀값
- 모든 trial과 모든 패널 블록 시작 전에 private receipt에 다음을 기록한다.
  - `codex_account_fp`: `sha256(tokens.account_id)` 앞 12자
  - `plan_claim`
  - `auth_expiry_margin_s`
- 기대값은 G0와 같은 지문 `57faa696f3a8`, plan `prolite`다. 필드 목록은 receipt 필드 (역사적 참조: `run-packets/receipts/trial-private-receipt.fields.md`; 해당 자료는 이 공개본에 포함되지 않음)에 있다.
- 만료 여유가 (단위 예상 시간 + 60분)보다 짧거나, 지문이나 plan이 바뀌면 시작하지 않거나 중단하고 조율자에게 알린다.
- 토큰, 키, `private-secrets/` 내용은 열람·출력·해시·게시하지 않는다. run-log에는 지문 앞자리와 사용률(%)만 적는다.

### 1.2.1 승인된 계정 교체 · 2026-09-27 06:02:09 KST

사용자가 계정 교체 후 재개를 지시했다. 원래 G0 `57faa696f3a8`/`prolite`와 그 결과·시작 거부는 보존하며, 새 P/G 실행은 `[account-withheld]`/`pro`를 G0로 사용하는 `jev-panel-r1`/run-id `-r1`에서 시작한다. 구독 경로·Astra xhigh·Jev1.13.0·입력·규모·판정규칙은 유지한다. 단위 도중 계정 또는 plan 변경은 계속 거부한다. 같은 공통 프로그램 원장의 모델 호출 누계는 보존하고, quota 비율 보정은 현재 계정·plan의 종료 관측만 사용한다. 이전 계정과의 결과 비교에서는 계정·plan 변경을 환경 차이로 공개한다.

`--quota-live` 모드의 P/G 단위 종료에 사용량 스냅샷을 연결한다. 조회 실패는 unknown이며0으로 채우지 않는다. 새 private `run_guards.py`·`track_common.py`는 오프라인 검증 후 새 freeze에서 해시로 묶고, 이전 동결 파일을 고치지 않는다. 초기화권 소비는 수행하지 않았다.

### 1.2.2 새 계정 실행기의 사전 경계 수리 · 2026-09-27 06:21:33 KST

P-r1은 실행기 registry 초기화 누락으로 모델 호출 전에 종료했다. 같은 소스 #2와 입력으로 P-r2 새 freeze를 만들고 공통 private 초기화에서 기존 `bootstrap_builtins(policy_sources=EMPTY_POLICY_SOURCES)`를 호출했다. P-r1 오류·quota ledger는 보존한다. WHAM의 raw `used_percent`는 퍼센트 값으로 읽으며, 값 1을 100%로 추정하던 legacy 변환은 새 private guard에서 사용하지 않는다. 계정 전환과 초기화 수리는 판정 프롬프트·스키마·모델·규모를 바꾸지 않았다.

U1은 호출 전에 선택 데이터 적합 범위를 명시한다: headline 144개는 주지표, 봉투 밖 16개는 별도 서술, 온도와 τ는 selection 160개를 기존 §5 규칙으로 처리한다. 유효 출력만 온도 적합에 쓰고 무효 Jev는 τ 평가에서 fallback으로 보낸다. 양쪽 U1 prospective spec은 입력·gold·분석기 해시와 이 문장을 묶었다. test·외부 데이터를 적합에 쓰지 않는다.

### 1.3 고정 SHA에 들어 있어야 할 기능(G-1 확인 목록)
1. V1: Astra Choice `{verdict, probabilities}`, Noul 조건별 확률, 스키마·프롬프트 digest.
2. 검증기: 완료 판정 패널의 Choice 확률 합 허용은 0.025다. I-패널(U0c-i·U6a)은 E2E intent helper와 같은 Jev Choice 엄격 합 허용치 1e-5를 쓴다. Score 기대값 허용치는 설정값으로 두고 U0b 뒤 동결한다(§4.1).
3. checker: V1, `verification_primitive`, `candidate_judge` purpose.
4. 패널 runner: `MatchedVerifierAdapter`를 직접 호출하고, Choice와 Noul을 교차 dispatch하며, 두 attempts 파일을 쓴다. 대체 규칙, pacing, heartbeat 포함.
5. V3 안정성 hook: 기준 순서 역전, 바꿔쓴 질문 세트.
6. 지표 모듈(§3 공식)과 합성 테스트.
7. Score-S 하네스: `delegate_task(best_of=4)`로 풀을 한 번 생성하고, 동결 풀을 `judge_candidates`에 주입한다. 양순서, 해시 동률, listwise 참조 포함. (v2.2) Jev selector에는 `sum_tolerance=0.025`와 동결 `score_tolerance`를 명시 인자로 넘긴다. 코드 기본값은 둘 다 엄격 1e-5다(§3.7).
8. I-패널 하네스. 통합 0029는 고정 #2 후보에 들어 있다. U0c-i·U6a는 `PanelUnit(judgment="intent", mode="paired-latency", max_concurrency=2)`로 한 가족의 Astra·Jev 호출을 함께 보낸다. `InboxDecisionAdapter`가 E2E `analyze_request`와 같은 payload·질문·수용 검사를 쓴다. Jev 확률 합 허용은 엄격 1e-5다(§2.3, §4.1).
9. Harbor runner 재고정: verdict-e2e, noul-verdict conditions(`validate_observations`에 primitive 전달), intent runner(`duration_ms` 수정).
10. host 수준 Jev 원장(§9).
11. arm C 코드(없으면 C는 미실행).
12. (v2) 쌍 동시 디스패처: 슬롯의 arm을 동시에 띄우고, 선택적으로 에이전트 시작 barrier를 둔다. 슬롯 동기와 동시 부하를 기록하고, 전역 실행 잠금(E·P·G·solo)을 건다(§2.4–§2.6).
13. (v2) U3 쌍 동시 지연 모드: 상태마다 A와 B를 동시에 보내고, 한 번에 쌍 하나만 진행한다. (v2.2 보완 3) 통합 0025의 `mode="paired-latency"`로 들어왔다(PR head `020caa1dc`).
14. (v2.2) U2s 연결 코드: 통합 0019·0022의 `verdict_panel_runner.stability_report`다(§3.7-3). 고정 SHA에 두 패치가 들어 있어야 한다.
15. (v2.2) private runner 계약(통합 GAP 2): freeze 셀 필드 5개와 private receipt 경로, 정본 열 이름(§2.4, §3.7).
16. (v2.2 보완) Choice 단독 `PanelUnit`(통합 0025, PR head `020caa1dc`에 반영): X1a·X1·U3가 쓴다.
    - X1 채점은 0026이다: 분석 모듈 `external_binary.py`, 1차 `x1_binary_verdict_accuracy_delta`.
    - 보존된 attempt와의 연결, CLI, 서술 지표는 0030이다(고정 #2, v2.2 보완 4에서 번호 정정).
17. (v2.2 보완 5) Score-S 제한 동시 실행과 호출별 시간 제한(통합 0024, 고정 #1·#2 후보 소스에 반영): U0b·U4·U5s·X2. 인자는 `max_concurrency=4`, `timeouts={"llm": 180, "jev": 60}`이다. listwise는 Astra 호출이라 llm 값을 쓴다.

### 1.4 공유 계정의 한계(v2)
- 같은 Codex 계정(fp `57faa696f3a8`)을 영상 작업 Codex 세션이 동시에 쓴다(사용자 승인). 그 세션의 호출 수, 시각, 토큰은 관측할 수 없다.
- 영향:
  - 서버 쪽 큐잉과 요율 제한이 우리 호출의 지연과 한도 오류에 섞일 수 있다.
  - quota 사용률 변화(Δused%)에 외부 사용이 포함된다.
  - 시각이 다른 호출끼리, 그리고 M4 등 이전 계정·시점과의 지연 비교는 신뢰할 수 없다.
- 대응:
  - trial과 블록마다 `external_account_usage="unknown"`을 기록한다(§2.6).
  - 지연은 **같은 시각에 함께 실행된 쌍의 내부 비교**를 1차 해석으로 둔다(§3.6).
  - quota 보정 계수 r은 외부 사용을 빼지 않은 보수적 값으로 쓴다(§7).
  - 외부 사용 때문에 생긴 한도 오류도 인프라 무효로 처리한다. 우리 탓인지 여부로 분류를 바꾸지 않는다.
- 결과 문서, 영상, 게시물에는 이 한계를 적는다. "단독 계정·통제된 부하에서의 지연"이라고 서술하지 않는다.

### 1.5 설계에서 오는 누설: m 요인(v2.1)
- **사실.** quad 설계는 m 칸에서 f2 관측을 삭제한다. 그래서 공개 test states나 Score 풀만 있어도 같은 quad 안에서 lookup 개수를 비교하면 missing_evidence(m) 요인이 **216/216 복원**된다(제2 저작자 확인).
- **범위.** 이 누설은 m 요인에 한정되고 contradiction(c) 요인에는 미치지 않는다. 판정 엔진에는 전달되지 않는다. 사람과 도구가 공개 파일을 대조할 때만 생긴다. selection split도 구조는 같지만 봉인 대상이 아니다.
- **완화 규칙(사전 등록).**
  1. **판정 엔진은 상태를 하나씩만 받는다.** 한 호출에 다른 상태, quad, 클러스터 정보가 없다. 교차 비교는 모델 경로에 존재하지 않는다.
  2. **test dispatch 순서는 같은 quad가 이웃하지 않게 섞는다**(§8.1 간격 규칙, 창 4).
  3. **τ와 온도는 selection에서만 정한다.** test 전에 코드, 프롬프트, 설정을 동결한다(§5). **test 공개 파일로 무엇도 튜닝하지 않는다.** 분석과 보고서 작성 중에도 공개 파일에서 복원한 m 정보를 gold 대용으로 쓰지 않는다.
  4. **Score 통제 풀(U4·U0b)에서 후보 사이의 근거 비교는 과제의 정당한 일부다.** selector는 한 풀의 후보 4개를 함께 보므로, 근거 줄이 빠진 후보를 형제 후보와 비교해 알아볼 수 있다. U4 결과는 "근거 비교가 가능한 통제 풀"에서의 선택 성능으로 서술한다. 자연 풀(U5)과 같은 난이도로 해석하지 않는다.
- 보고서와 영상의 한계 절에 "공개 파일에서 m 요인이 복원 가능하나, 모델은 상태를 하나씩만 보았고 모든 선택은 test 전에 동결되었다"를 적는다.

### 1.6 고정 SHA 두 개(v2.2 보완 4, 조율자 결정)

| 고정 | 커밋 | 들어 있는 통합 패치 | 쓰는 단위 |
|---|---|---|---|
| #1 | PR head `7cd052649`(CI 15/15 확인) | 0027까지(0024 Score-S, 0025 Choice 단독·U3, 0026 X1 채점, 0027 호출 실패 분류표) | E 트랙: U0d, U0e, U0c(Harbor 부분), 이후 U8c, U8n, U6b, U0f, U7r0, U7r1 |
| #2 | `2f2b494d605c9306dcf1d94a2394e7576e959ace`(소스 고정 확인; 단위 동결 전) | #1 + 0028(일시적 429 처리, §4.1), 0029(I-패널 하네스), 0030(X1 연결·서술 지표) | P·G·solo: U0a, U0b, U0c-i(I-패널 batch), U1, U2, U2s, U3, U4, U5, U6a, X1a, X1, X2 |

- 이유: 사용자 재생 검토라는 사람 게이트를 빨리 열기 위해 E 트랙을 먼저 고정한다.
- 실제 통제: E 트랙 실행과 E 단위의 표·분석은 모두 #1 원본 checkout `[local-path-withheld] 코드를 쓴다. 각 run-spec `revision`도 자기 트랙의 SHA로 묶는다. #2의 코드를 E 단위에 섞거나 #1 checkout을 덮어쓰지 않는다.
- #1→#2 후보 변경: 패널 runner·Score-S·I-패널·X1 분석과 함께 E helper 모듈 `evals/benchmarks/decision_handoff.py`도 바뀌었다. 0029가 `DecisionHandoffTool`의 기존 요청 작성·수용 검사를 `_decision_request`·`_admit`으로 추출하고, 이를 쓰는 `InboxDecisionAdapter`를 더했다. 따라서 두 커밋의 E 관련 소스가 같다는 주장은 하지 않는다.
- 회귀 근거: `tests/evals/benchmarks/test_decision_handoff.py::test_helper_requests_admission_and_outputs_are_unchanged`는 10개 합성 시나리오의 요청·수용 결과·관측 이벤트 바이트를 0029 이전 digest와 비교한다. 성공(single/inbox, Astra/Jev), 거부, 후보 밖 target, 응답 모델 변경, Jev 합 위반, 503, 연결 실패를 포함한다. 기준 `0a90cf8fe`의 `decision_handoff.py`는 #1과 SHA-256 `82bbf1d6ef071377b92b650702cda4583bd916e9eed6bf72cb41d23210e1948c`로 같고, 후보 `2f2b494d6`에서 이 회귀 1개(10 시나리오)가 통과했다. 이는 해당 합성 경로의 바이트 보존 근거이며 live E2E 검증을 대신하지 않는다.
- #2 확정 전에 정확한 head의 필수 CI와 G-3를 확인하고, `git diff --stat #1..#2`·위 리팩터·회귀 결과·E 실행 및 분석의 #1 유지 조건을 run-log와 해당 `freeze.json`에 기록한다. 후보의 비교 범위는 14파일, 2,684줄 추가·230줄 삭제다. 이후 head가 바뀌면 diff와 회귀를 다시 확인한다.
- 위 추출 리팩터 외에 E 동작·프롬프트·스키마·분석 경로가 바뀌거나, 회귀가 실패하거나, E 실행·분석을 #1에 묶을 수 없으면 #2 동결을 멈추고 조율자에게 보고한다. 이 문구 정정 자체는 동결이나 실행 승인이 아니다.

### 1.7 U0d 수집기 오류와 수정판 재실행(2026-09-27, 사용자 승인)

- #1의 U0d 첫 natural A/B 2셀을 실행한 뒤 공유 수집기 오류로 dispatch가 중단됐다. runtime 및 metadata는 정상 종료 `natural`, 네이티브 최종 판정과 독립 oracle은 pass였으나, 수집기가 `end_turn`만 허용했다. 원본 2셀은 validity=invalid, outcome=unknown, 단위 1차값은 not-measurable로 보존한다. 관측 Astra7/Jev1이며 추가 슬롯·U0e·U0c 실호출은 없다. 원본 무효 결과를 소급 통과로 바꾸지 않는다.
- 수정 후보 #3은 `7f32ff272d1b07a6404c593e74dad727857e0bd8`다. #2 대비 실제 코드 변경은 `scripts/eval/check_harbor_observations.py`의 성공 종료 상태 검사이며 runtime이 소유한 `is_successful_task_termination`을 재사용한다. 종료값 일치·최종 judge·독립 oracle·오류 없음 조건은 유지한다. 나머지는 fixture·회귀·CHANGELOG와 생성 mirror다. #2 대비 7파일 +61/-10이다.
- #1→#3에는 §1.6에 공개한 0029 E helper 리팩터도 포함된다. 이를 단순 수집기 변경만이라고 설명하지 않는다. 10시나리오 바이트 회귀와 새 고정의 CI·G-3를 확인한 뒤 **새 소스의 E 실행 및 새 lineage 승인을 받아야** #3를 E 단위에 쓸 수 있다. #1/#2 checkout과 기존 run 원본은 덮어쓰지 않는다.
- 승인 시 U0d→U0e→U0c를 `-r1` run ID의 새 폴더에서 수행하고, 무효 원본과 합치지 않는다. 모델·effort·workload·반복·동시성·분모·수용 기준은 유지한다. 기존 공통 PROGRAM의 quota·Jev 원장을 이어 써 이미 사용한 호출과 비용을 보존한다. 완료 뒤 사람 재생 검토에서 멈춘다.
- 사용자 재실행 승인(2026-09-27 03:47:49 KST)으로 E 새 lineage에는 #3를 쓴다. §1.6의 #1은 무효 원본 이력에 유지하고, P·G·solo #2는 변경하지 않는다. #3 CI와 G-3 확인 뒤 동결·실행하며 별도 모델/규모 변경이나 본실험·공개 승인은 포함하지 않는다.

## 2. 단위별 run-spec 초안(U0–U8, X1·X2)

### 2.1 공통 골격
⟨⟩는 동결할 때 채운다. 동결 파일에는 `<…>` 형태가 남으면 안 된다(`contract.py`가 거부한다).

```json
{
  "schema_id": "geode.eval-run-spec@1", "schema_version": 1,
  "run_id": "geode-jev-⟨primitive⟩-⟨phase⟩-⟨YYYYMMDD⟩",
  "created_at": "⟨RFC3339⟩",
  "preregistration": {"mode": "prospective", "status": "frozen", "frozen_at": "⟨≥created_at⟩",
    "live_test_approved": true, "operator": "User instruction via coordinator 2026-09-26; Run owner freeze"},
  "study": {"research_question": "⟨card⟩", "research_gap": "⟨card⟩", "hypothesis": "⟨card⟩",
    "primary_metric": {"name": "⟨§2.2⟩", "unit": "⟨ratio|s⟩", "direction": "⟨§2.2⟩",
      "aggregation": "⟨formula; invalid output = wrong⟩", "denominator": 0},
    "decision_rule": "⟨§3.4⟩", "invalidation_rule": "⟨§4⟩", "analysis_plan": "⟨§3; selection-freeze sha256 where relevant⟩"},
  "reproduction": {
    "geode": {"revision": "⟨PR head SHA⟩", "branch": "⟨topic⟩", "dirty": false},
    "harness": {"name": "⟨Harbor | GEODE panel runner⟩", "source": "⟨harbor==0.22.0; private runner.py sha256⟩", "revision": "⟨0.22.0 | runner sha256⟩"},
    "model": {"provider": "openai", "label": "gpt-6-astra", "route": "subscription", "reasoning": "xhigh"},
    "environment": {"platform": "⟨host⟩", "architecture": "arm64", "reset_strategy": "⟨§1.1⟩", "initial_state_ref": "sha256:⟨input manifest⟩"},
    "execution": {"command_redacted": "⟨…⟩", "ordered_workload_ids": ["⟨§8.1 order⟩"], "workload_ids_sha256": "⟨…⟩",
      "repetitions": 1, "seed_schedule": ["unseeded-provider-inference-repeat-0"], "max_concurrency": 4,
      "timeout_seconds": 180, "budget": {"kind": "combined", "limit": 0, "unit": "astra-xhigh-calls; jev-usd-program-cap-1.00"}},
    "comparison": {"claim_class": "diagnostic", "comparator": "⟨A/B/C arms⟩", "comparability": "direct", "promotion_authority": "none"}},
  "artifacts": {"native_results": "results.json", "measurement_results": null, "trajectory": "⟨E2E: trials/ | null⟩",
    "verifier_receipts": "⟨E2E | null⟩", "outcome_receipts": null, "attempts": "attempts.jsonl", "analysis": "analysis.json", "publication_manifest": null},
  "privacy": {"classification": "⟨internal | withheld(봉인 입력 단위)⟩", "redaction_boundary": "prompts, receipts, DBs, IDs, host paths withheld-private; key contents never persisted; actual charges unknown"}
}
```

`denominator`와 `budget.limit`의 0은 형식상 자리표시이고 §2.2 값으로 바꾼다. 패널 단위는 `max_concurrency=4`, `timeout_seconds=180`이다. Harbor 단위의 `max_concurrency`는 v2부터 슬롯의 arm 수(2, C 포함 3)이며 `timeout_seconds=210`이다. U3·U0c-i·U6a는 `paired-latency` 모드와 동시성 2를 쓴다. 단위별 실제 초안은 run-packets/run-specs/ (역사적 참조: `run-packets/run-specs/`; 해당 자료는 이 공개본에 포함되지 않음)에 있다. 동결 전까지 일부러 `PENDING` 값을 남겨 검증을 통과하지 못하게 해 두었다.

### 2.2 단위표
디렉터리는 03 런북의 `jev-<primitive>-<study>-<date>/<phase>/`를 따른다. Astra 상한은 `budget.limit`이다(패널은 계획의 약 105%, E2E는 롤아웃당 10회).

v2에서 마지막 열(창 W1/W2)은 참고용으로만 남긴다. quota는 일정 제약이 아니며, 실행 트랙과 순서는 §2.5와 [스케줄](schedule.md)을 따른다.

| 단위 | run_id(`geode-jev-` 다음, 날짜 생략) | 입력 | Astra 계획/상한 | Jev | 1차 지표(방향, 분모) | 분류 | 창(v1, 참고) |
|---|---|---|---|---|---|---|---|
| U0a | `verdict-panel-admission-choice` / `-noul` | selection 8 상태(칸당 2) × {Choice, Noul} × 2 엔진. v2.2 보완에서 run 두 개(U0a-c, U0a-n)로 나눴다 | 8/9씩 | 8씩 | `panel_admission_admitted_ratio`(max, 16씩) | internal | W1 |
| U0b | `score-bestof-admission` | 통제 풀 2 × 2순서 × 3 selector + 자연 풀 1개 생성·선택 | ≈28/40 | 6 | `score_admission_valid_selection_ratio`(max, 18) | internal | W1 |
| U0c / U0c-i | `choice-intent-admission` / `choice-intent-panel-admission` | `inbox-admission` A→B(Harbor 2셀, 고정 #1) / I-패널 admission 4 가족 × 2 엔진(고정 #2, 0029; `judgment="intent"`, `paired-latency`, 동시성 2). v2.2 보완 4에서 나눴다 | ≈10/20 · 4/5 | ≈1 · 4 | 준비된 admission 성공(max, 2) / `intent_panel_admission_admitted_ratio`(max, 8) | internal | W1 |
| U0d | `verdict-e2e-admission` | 자연 A·B, 주입 (1,1) A·B(Choice). v2.1 원천은 selection `cl-s15-shoes`·`cl-s05-fishing` | ≈22/40 | ≈3 | `verdict_e2e_admission_success`(max, 4) | internal | W1 |
| U0e | `noul-verdict-admission` | 주입 (1,1) A·B(Noul), `cl-s05-fishing` | ≈12/20 | ≈2 | `noul_e2e_admission_success`(max, 2) | internal | W1 |
| U1c / U1n | `verdict-panel-selection-choice` / `-noul` | selection 160 상태 | 160/168씩 | 160씩 | `m7sel_choice_paired_accuracy_delta` / `m7sel_noul_joint_accuracy_delta`(target, N_sel_in) | internal | W1 |
| τ | `selection-freeze.json` | U1 출력만 사용(§5) | 0 | 0 | — | internal | W1 |
| U2c / U2n | `verdict-panel-test-choice` / `-noul` | test 240 상태 | 240/252씩 | 240씩 | `m7_choice_paired_accuracy_delta` / `m7_noul_joint_accuracy_delta`(target, N_test_in) | **withheld** | W1 |
| U2s | `verdict-panel-stability-choice` / `-noul` | test 24 상태 × 4 변형 × 2 질문. run 두 개(U2s-c, U2s-n) | 96/101씩 | 96씩 | `jev_choice_pair_consistency` / `jev_noul_pair_consistency`(max, 24씩, 통합 0022의 run별 primary, §3.7-3) | withheld | W1 |
| U3 | `verdict-panel-latency` | test 120 상태, Choice(상태마다 A와 B 동시, 단독 슬롯). `mode="paired-latency"`, `max_concurrency=2`, `pacing_s=1.0`, `timeout_seconds=180`(Jev 60초는 코드 상수) | 120/126 | 120 | `paired_median_latency_delta_s`(target, 1, 단위 s) | withheld | W1 |
| U4 | `score-bestof-controlled` | 통제 풀 80 × 2순서 × {Astra pointwise, listwise} + Jev | 320/336 | 160 | `score_ctl_top1_delta`(target, 80) | internal | W2 |
| U5p / U5s | `score-bestof-pool` / `-selection` | 자연 12 task 풀 생성 1회 → 동결 풀 × 2순서 | ≈192/300 · 48/52 | 0 · 24 | `natural_pool_complete_ratio`(max, 12) / `score_nat_top1_delta`(target, N_pool_valid) | internal | W2 |
| U6a | `choice-intent-panel` | I-패널 220 항목(40 가족, 설계자 저작; `judgment="intent"`, `paired-latency`, 동시성 2) | ≈40/44 | ≈40 | `intent_joint_accuracy_delta`(target, 220) | withheld | W2 |
| U6b | `choice-intent-natural` | 준비된 자연 6셀 | ≈30/60 | ≈3 | `strict_task_success_delta`(target, 3) | internal | W2 |
| U0f(조건부) | `verdict-e2e-cascade-admission` | C 자연 1 + C 주입 1 | ≈12/20 | ≈2 | `cascade_e2e_admission_success`(max, 2) | internal | W2 |
| U7r0 / U7r1 | `verdict-e2e-natural-r0` / `-r1` | 자연 12 task × {A, B(, C)} | ≈103/240씩(C 포함 시 360) | ≈15씩 | `m8n_strict_success_delta`(target, 12) | internal | W2 |
| U8c | `verdict-e2e-injection` | 3칸 × 6 task × {A-Choice, B-Choice} = 36 | ≈200/360 | ≈36 | `m8i_choice_recovery_delta`(target, 18) | internal | W2 |
| U8n | `noul-verdict-conditions` | 3칸 × 6 task × {A-Noul, B-Noul} = 36 | ≈200/360 | ≈36 | `m8i_noul_recovery_delta`(target, 18) | internal | W2 |
| X1a(v2.2 보완) | `external-cuavb-choice-admission` | X1의 가장 긴 두 상태 × Choice × 2 엔진 | 2/3 | 2 | `x1_admission_admitted_ratio`(max, 4). 0025 코드 차단 해제 | internal | — |
| X1(v2.2) | `external-cuavb-choice` | CUAVerifierBench 변환 239 상태 × Choice × 2 엔진 | 239/251 | 239 | `x1_binary_verdict_accuracy_delta`(target, 239). 0030 코드 차단 해제; X1a·selection 동결 선행(§11.10) | internal(공개 등급 §11.8) | — |
| X2(v2.2) | `external-m2w-score` | Mind2Web test 3 split 240 풀, K=4 × 2순서 × {Astra pointwise, listwise} + Jev | 960/1008 | 480 | `x2_score_top1_delta`(target, 240). 동시성 4; U0b 허용치 동결 선행 | internal(공개 등급 §11.8) | — |

- 합계(v2.2 보완): Astra 약 3,641호출(X1a 2, X1 239, X2 960 포함, C 포함 시 약 +100), Jev 약 2,194호출. v2.1까지의 합계는 Astra 약 2,440, Jev 약 1,490이었다.
- 반복: U7만 2회이며, 반복마다 run-spec을 나눈다(`seed_schedule=["unseeded-provider-inference-repeat-⟨r⟩"]`). 나머지는 1회다. 안정성 변형은 workload ID에 넣는다(`<state>#rep1`, `#rep2`, `#order-rev`, `#para`).
- run-spec 하나에 롤아웃은 36개 이하다.
- 셀 순서: E2E는 §2.4의 쌍 동시 슬롯 규칙(띄우는 순서 교대)을 따른다. 패널은 상태마다 [A-Choice, B-Choice, A-Noul, B-Noul]의 순서를 4×4 Latin 방진으로 회전한다.

### 2.3 입력 구조(G-2 요구)
- **패널.** 90 quad(같은 task·항목의 (c,m) 네 변형) = 360 상태, 여기에 봉투 밖 40 상태를 더해 총 400 상태다.
  - 소스 클러스터는 40개 이상이고, 클러스터당 10 상태 이하다.
  - 클러스터 단위로 40/60 split을 한다(예상 selection 160 / test 240).
  - 봉투 밖 층(스타일 적대, 유도 검증, 무참조 문장)은 headline 분모에서 뺀다.
  - **selection split은 v2.1에서 저작을 마쳤다**(panel-selection (역사적 참조: `panel-selection/README.md`; 해당 자료는 이 공개본에 포함되지 않음)).
    - 18 클러스터: en 10, ko 7, mixed 1(한국어 계열 44%). 160 상태 = headline 144(칸마다 36) + 봉투 밖 16.
    - `verdict_panel check`를 문제 0건으로 통과했다. manifest sha256은 `0c0a64b1…`, gold는 `8a339cf0…`다.
  - test 27개와 합치면 45 클러스터, selection 비율 40%, 두 split의 한국어 비율 각 44%다. `--final`의 수치 조건을 모두 만족한다.
  - 두 split을 합친 `--final` 실행(요청 문장 중복 검사 포함)에는 봉인된 test 원본이 필요하다. 봉인 접근 담당이 돌린다.
- **gold.** 구조화된 후보 주장 × 관측 × 계약에서 규칙으로 (c, m)을 계산한다.
  - verdict는 c면 contradicted, 아니고 m이면 insufficient_evidence, 둘 다 아니면 supported다.
  - 규칙 스크립트의 해시를 동결한다.
- **Score.**
  - 통제 풀 80개: selection 36 + test 54 = quad 90개를 `sha256(pool_id + selection gold_sha256 + test gold_sha256)` 순서로 정렬한 앞 80개다(v2.1 salt 명시). 81–82번째는 U0b admission, 나머지는 예비다. v2에서 정정했다. 클러스터마다 quad가 정확히 2개라 v1의 "클러스터당 2개"로는 80개를 고를 수 없다. 등급은 supported 3, (0,1) 2, (1,0)·(1,1) 0이다.
  - 자연 task 12개: 기존 inbox oracle의 항목 정답 수로 등급을 매긴다.
  - G 트랙(U0b 자연 풀·U5p)의 생성 지시문은 `run-packets/freeze/natural-task.template.txt`다(SHA-256 `4202becf1707781de1379a1703595869762b34be2b50d65817900940c6e69f94`). 기존 `{contract}`·`{orders}`·`{inbox}` 구성에 “Use only the order records and the inbox below; do not look up or fetch anything else.”를 더했다. 드라이버의 `--task-template`과 run-spec 입력 참조에 이 파일·해시를 묶는다. admission 이후 문구를 바꾸면 영향을 받는 단위를 새 lineage로 시작한다.
- **held-out 재빌드(v2.2, 통합 0015).** 공개 test states의 `tool_call_id`와 공개 풀의 후보 순서가 원래 ID에서 파생되던 누설 경로를 막는 수정이다. 제2 저작자가 공개 파일을 다시 만들고, `gold_sha256`이 이전 값(`f73f0d87…`)과 같은지 확인한다.
  - 바뀌는 것: 공개 test manifest, states, pools의 해시. 그래서 U2c·U2n·U2s·U3의 dispatch 순서와 `workload_ids_sha256`, U4·U0b의 입력 참조가 바뀐다.
  - 그대로인 것: 별칭 ID 집합, gold, U2s·U3 부분집합(gold 기반 선정), 통제 풀 선정.
  - `subsets.test.json`은 새 공개 manifest 해시(`alias_manifest_sha256`)로 다시 발급받아야 한다. 생성기는 불일치를 거부하고, test gold가 바뀌어도 멈춘다.
  - **도착·반영(23:5x).** 재빌드 공개본은 `handoff-snapshot-20260926/heldout-public/`에 있다. sha256은 manifest `9fc1e80d…`, states `b4b79d5e…`, pools `bae08423…`, subsets `e59f41d9…`이고 조율자 값과 일치했다.
    - gold `f73f0d87…`, pools-graded `1efe6377…`, 별칭 `ee3942fa…`, 통제 풀 순서는 그대로다. U2s·U3 ID 24/120도 그대로이고 `alias_manifest_sha256`만 새 manifest를 가리킨다.
    - 초안을 새 공개본으로 다시 만들었다. 이전 공개본(manifest `d9ae7568…`)은 `superseded-20260926/`에 있다.
- **E2E 원천(v2.2: 옵션 E 채택).**
  - 배경(v2.1 검토): test 클러스터에서 과제를 파생하면 모델 경로로는 새지 않는다. 그러나 **사람 경로로는 test gold가 샌다.** oracle 기대 답이 (0,0) 상태의 답과 같고, 주입 후보를 gold에서 만들며, verifier receipt와 재생 화면에 이것이 드러난다. 상세는 E2E payload 사양 (역사적 참조: `run-packets/e2e-payload/README.md`; 해당 자료는 이 공개본에 포함되지 않음)에 있다.
  - **채택: 옵션 E.** 제2 저작자가 패널 밖 E2E 전용 inbox 원천 20개를 새로 쓰고 봉인한다. 자연 12, 주입 6, 예비 2다.
    - 봉인 원천은 `e2e-sealed-DO-NOT-OPEN/`에 있다. Run 담당은 열지 않고, 공개 목록의 ID와 sha256만 쓴다.
    - 공개 목록은 `run-packets/e2e-payload/e2e-sources.json`이다(사양 README §3 필드).
    - 순위는 `sha256(source_id + salt)` 오름차순이다. salt는 원천 20개의 파일 sha256을 정렬해 이은 문자열의 sha256이다. 1–12위는 자연, 13–18위는 주입, 19–20위는 예비다.
    - 생성기는 공개 digest만으로 salt와 순위·역할을 다시 계산하고, 다르면 거부한다. 그래서 저작자가 역할을 고를 수 없다.
    - **도착·반영(23:5x).** 목록 sha256 `d5e84738…`, salt `6139b86d…`, 봉인 쪽 seal manifest `a5a10389…`이다. 생성기가 salt와 순위·역할을 다시 계산해 통과했고, U7r0·U7r1·U8c·U8n의 workload와 슬롯 행렬을 다시 만들었다. 자연 1위는 `e2e-golfballs`, 주입 1위(전체 13위)는 `e2e-telescopes`다.
    - 원천이 패널 gold와 무관하므로 U8은 unseal을 기다리지 않는다. U7은 arm C 결정 때문에 여전히 unseal 뒤에 온다(§6).
  - **기각: 옵션 T+**(test 파생을 유지하고 U7·U8을 unseal 뒤로 미룸).
    - U8이 U2c·U2n·U2s·U3와 unseal 뒤로 묶여 E 트랙 시작이 늦어진다.
    - payload를 봉인 접근 담당이 만들어야 한다.
    - E2E 과제가 패널 test 내용과 겹쳐, 두 결과가 서로 독립적이지 않다.
  - **기각: 옵션 S**(selection 클러스터에서 파생).
    - selection은 설계자가 저작했고 τ·T 적합에 쓰인다. 그래서 arm C의 τ가 표본 안에 들어간다.
    - selection 18 클러스터 가운데 15개가 이미 U5p(12), U0b(1), admission(2)에 배정되어 있다. 18개를 새로 낼 수 없다.
  - **admission 원천은 selection 클러스터다(v2.1부터).** 14번 `cl-s15-shoes`는 자연, 15번 `cl-s05-fishing`은 주입 c1m1이다. 봉인 대상이 아니다. `noul_conditions build`로 c1m0·c0m1·c1m1 세 칸이 모두 계획대로 생성되는 것을 무모델 예행으로 확인했다.
  - 주입 칸: (1,0)은 관측 후 모순, (0,1)은 관측 전 조기 주장, (1,1)은 계약 위반 쓰기 주장과 미관측 상태 주장을 한 후보에 담는다.
  - 모두 `validate_inbox_case`와 `validate_verification_intervention`을 통과해야 한다.
- **I-패널.** v2.1에서 저작했다(i-panel (역사적 참조: `run-packets/i-panel/README.md`; 해당 자료는 이 공개본에 포함되지 않음)).
  - 규모: analysis 40 가족, 220 항목(U6a 분모 220). admission 4 가족, 20 항목(U0c-i; Harbor admission U0c와 별도).
  - 한 가족을 하나의 입력으로 두 엔진에 함께 보내며 `judgment="intent"`, `mode="paired-latency"`, `max_concurrency=2`, `pacing_s=1.0`, 호출 제한 Astra 180초·Jev 60초를 쓴다. Astra는 라벨만 반환하고, Jev Choice는 E2E helper와 같은 엄격 합 허용치 1e-5를 쓴다. 완료 판정 패널의 0.025를 적용하지 않는다.
  - 분석은 `python -m evals.benchmarks.verdict_panel_runner intent --run-spec … --run-dir … --panel … --meta … [--record]`로 연결한다. `--record`는 분석 산출물을 배타 생성하므로 한 번만 쓴다. I-패널 지연은 서술용이며, 모드 이름이 U3 외 지연 주장 범위를 늘리지는 않는다.
  - 모든 가족이 `validate_inbox_case`를 통과했다. 정답 규칙은 LABEL-RULES (역사적 참조: `run-packets/i-panel/LABEL-RULES.md`; 해당 자료는 이 공개본에 포함되지 않음)에 있다.
  - **설계자가 저작했으므로 held-out이 아니다.** U6a는 "설계자 저작 진단"으로 서술한다.
- **바꿔쓴 질문 세트(`#para`)**: 제2 저작자가 썼다(`para.test.jsonl` `e91a2d2e…`, Choice 1행·Noul 1행, `PanelUnit.paraphrases` 형식). U2s 입력 참조에 해시를 넣었다.
- **외부 데이터(X1·X2, v2.2).** 외부 데이터 담당이 `external/{cuavb,m2w}/`에 변환본과 manifest를 둔다. 요구 조건과 대기 항목은 §11.2, §11.10에 있다.

### 2.4 쌍 동시 실행(v2)
- **슬롯.** (단위, 과제[, 칸], 반복)마다 슬롯 하나를 둔다.
  - 슬롯에는 비교 arm이 모두 들어간다: A와 B, C 승인 시 A·B·C. U8은 A-Choice와 B-Choice, 또는 A-Noul과 B-Noul이다.
  - arm마다 새 agent 컨테이너와 별도 verifier를 쓴다.
  - 전체 행렬은 슬롯 행렬 (역사적 참조: `run-packets/cells/e2e-slots.md`; 해당 자료는 이 공개본에 포함되지 않음)에 있다.
- **동시 시작.** 디스패처가 같은 호스트 시각에 모든 arm을 띄운다(`host_launch_utc`).
  - 선택 사항으로 barrier를 쓸 수 있다: 설치를 마친 arm이 형제 arm을 최대 120초 기다렸다가 함께 root 실행을 시작한다(`barrier_used`).
- **허용 오차.**
  - `dispatch_skew_s`는 1초 이하여야 한다. 넘으면 디스패처 결함으로 보고 단위를 중단한다(인프라 무효).
  - `agent_start_skew_s`가 30초 이하면 `pair_sync=true`다. 넘어도 유효성과 성공·복구 분석에는 영향이 없다. 쌍 내부 지연 해석(§3.6)에서만 따로 보고한다.
- **다음 슬롯.** 슬롯의 모든 arm이 cleanup까지 끝난 뒤에 시작한다. 워치독 930초는 trial마다 적용한다.
- **띄우는 순서(`position`) 교대.**
  - U7r*r*: 과제 순위 *i*에 대해 (*i*−1+*r*)가 짝수면 A,B, 홀수면 B,A. C를 넣으면 (*i*−1+*r*) mod 3에 따라 ABC, BCA, CAB. 과제마다 두 반복에서 먼저 뜨는 arm이 서로 바뀐다.
  - U8c: 슬롯 번호 *s*에 대해 (*s*−1)이 짝수면 A가 먼저다. U8n은 반대다.
  - U8의 칸 순서는 과제마다 회전한다: (c1m0, c0m1, c1m1) → (c0m1, c1m1, c1m0) → (c1m1, c1m0, c0m1).
  - U6b는 준비된 프로토콜 순서(explicit A/B, context B/A, korean A/B)를 따른다.
  - 띄운 순서와 실제 에이전트 시작 순서를 둘 다 기록한다.
- **Replay 화면 좌우.** 실행 순서와 무관하게 A(LLM)는 왼쪽, B(Jev)는 오른쪽이다. C는 부록이다.
- **Replay와의 관계.** Replay 쌍은 같은 슬롯의 두 trial이므로, 실제로 같은 시간대에 실행된 녹화다. 사전 선정(§8)은 바꾸지 않는다. `pair_sync=false`여도 교체하지 않고 skew를 캡션에 적는다.
- **한 arm이 인프라 무효일 때.** 형제 arm은 끝까지 실행해 보존한다. 다음 슬롯은 시작하지 않고(E2E 첫 무효 중단 규칙), 해당 단위 primary는 not-measurable이 된다.
- **자원.** U0d에서 trial 2개 동시 실행을 확인한다. C가 승인되면 U7 첫 슬롯 전에 모델 없이 컨테이너 3개 동시 기동을 점검한다(infra proof 확장). setup 시간 초과는 인프라 무효다.
- **열 이름(v2.2).** 정본은 조율자 목록의 `slot_id`, `dispatch_skew_s`, `agent_start_skew_s`, `pair_sync`, `concurrent_trials`, `external_account_usage`다.
  - v2 Run 초안의 `pair_launch_skew_s`, `pair_agent_start_skew_s`, `concurrent_trials_active`, `same_account_external_usage`는 폐기 예정 별칭이다.
  - 코드(통합 0017, `handoff_tables`)는 정본과 별칭을 모두 읽는다. 같은 receipt에서 두 값이 다르거나, `pair_sync`가 30초 규칙과 모순되면 거부한다. `external_account_usage`는 receipt와 무관하게 항상 `unknown`으로 쓴다.
  - 새 receipt와 문서는 정본 이름만 쓴다(receipt 필드 (역사적 참조: `run-packets/receipts/trial-private-receipt.fields.md`; 해당 자료는 이 공개본에 포함되지 않음)).

### 2.5 트랙과 비중첩(v2)
- **트랙.**
  - E: Harbor 쌍 슬롯. U0c의 Harbor 셀, U0d, U0e, U0f, U6b, U7, U8.
  - P: 판정 패널. U0a, U0b의 선택 호출, U0c의 I-패널, U1, U2c/U2n/U2s, U4, U5s, U6a.
  - G: 후보 생성. U0b의 자연 풀, U5p.
  - solo: U3.
- **전역 실행 잠금.** 호스트 잠금 파일 하나로 한 번에 한 트랙만 실행한다.
  - E 단위가 시작되면 그 단위의 슬롯이 모두 끝날 때까지 다른 트랙은 시작하지 않는다.
  - P와 G 단위는 시작하면 끝까지 간다.
- **우선순위.** 준비된 단위가 여럿이면 E가 먼저다. 패널은 E2E가 없는 빈 시간에 돈다. E가 게이트(재생 검토, arm C 결정)로 막혀 있을 때 P와 G를 진행한다.
- **U3.** 다른 트랙이 모두 멈춘 상태에서만 돌린다. 우리 쪽 무거운 작업(데이터 정제 배치, 다른 Codex 사용, Docker 빌드)도 멈춘다. 영상 세션은 통제할 수 없으므로 unknown이다.
- **순서.** 선행 의존(U0 → U1 → τ 동결 → U2c/U2n/U2s/U3 → arm C 결정 → U7)은 반드시 지킨다. E 트랙의 U8과 U6b는 재생 검토만 통과하면 M7과 독립적으로 진행할 수 있다. 운영 진행표는 [스케줄](schedule.md) §3이다.
- **잠금 위반.** 겹침이 생기면 나중에 시작한 단위를 중단하고 `failure_class=schedule_overlap`인 인프라 무효로 처리한다.

### 2.6 동시 부하 기록(v2)
- **E2E trial마다.**
  - `concurrent_trials`: 시작 시점에 같은 호스트에서 돌고 있는 다른 trial 수.
  - `overlapping_calls`(+`_observed`, `_missing_intervals`): 다른 trial의 호출과 시간 구간이 겹치는 수다. 데이터 담당이 `call_ledger` 구간으로 사후 계산하며, 구간이 없으면 null이다(03 §5).
  - `external_account_usage="unknown"`(항상). 설명용 `external_usage_reason="shared-account-video-session"`은 private receipt에만 둔다.
- **패널 호출마다.** `in_flight_panel_calls`, 같은 unknown 필드, heartbeat lag(`heartbeat.jsonl`).
- **해석.** 이 값들은 설명 변수로만 보고한다. 사전 등록에 없는 보정·회귀 분석은 하지 않는다.
- **필드 이름.** receipt 필드 (역사적 참조: `run-packets/receipts/trial-private-receipt.fields.md`; 해당 자료는 이 공개본에 포함되지 않음)에 있다. 새 열은 03 §5에 추가를 요청하는 것이며 데이터 담당이 확정한다.

## 3. 분석 계획과 지표

### 3.1 정답 정의
- **Choice**: 유효하고 verdict가 gold와 같으면 정답이다.
- **Noul 조건**: 유효하고 (p ≥ 0.5)가 gold와 같으면 정답이다. 두 엔진 모두 확률에 같은 임계를 쓴다. 두 조건이 모두 맞으면 joint 정답이다.
- **Score top-1**: 두 순서의 점수 평균 s̄로 argmax를 고른다. 동률은 `sha256(pool_id∥candidate_id)`가 가장 작은 후보다.
  - 선택이 oracle-best 집합에 들면 정답이다.
  - 어느 한 순서라도 무효이거나 fallback이면 오답이다.
  - listwise는 순서별 적중의 평균(0, 0.5, 1)이다.
- **intent**: intent와 target(목표가 없으면 `none`)이 모두 맞아야 joint 정답이다.
- **E2E strict 성공**: native reward 1 ∧ 판정 admission ∧ 소비 완전 ∧ 거짓 완료 0. intent는 여기에 잘못된 lookup 0과 추가 lookup 0이 더해진다.
  - 거짓 완료: 최종 판정이 통과인데 oracle이 실패한 경우.
  - 거짓 거부: oracle이 통과할 후보에 부정 판정을 낸 경우.
  - 복구: 첫 판정이 부정 → 이후 root가 소비 → 최종 oracle 통과.
  - (1,1) 1회 완전 복구: 수리 1라운드 뒤에 두 결함이 모두 해소된 경우.

### 3.2 지표 공식(파생 JSON에 분자/분모 JSON pointer로 바인딩, 구간 경계는 분모 1)

| 지표 | 정의 |
|---|---|
| 정확도 | 정답 수 / 계획 항목 수(무효 = 오답) |
| macro-F1 | 클래스별 F1의 평균. 무효는 gold 클래스의 FN이고 어떤 클래스의 FP도 아니다 |
| Brier | Choice: Σ_k (p_k − 1[k=y])². Noul: (p − y)². 유효 출력만 사용 |
| NLL | −ln max(p_y, 1e-6) |
| ECE | q ∈ [0,1]을 등폭 10구간으로 나눈다(마지막 구간은 1.0 포함). Σ_b (n_b/N_valid)·\|acc_b − mean q_b\| |
| q | Choice는 max_k p_k, Noul은 max(p, 1−p). Jev `confidence`는 별도 열에 둔다 |
| AUROC(오류 탐지) | 유효 출력에서 오답을 양성, 점수는 1−q. Mann–Whitney, 동률은 0.5. 한 클래스가 비면 not-measurable |
| risk–coverage | q 내림차순으로 수락한다. coverage = 수락/계획 항목, risk = 수락 중 오답/수락. 무효는 수락하지 않는다. AURC와 coverage 0.5·0.8의 risk를 보고한다 |
| pair consistency(v2.2) | U2s 1차. 같은 질문 rep1과 rep2의 결정이 둘 다 유효하고 같은 상태의 비율(엔진·질문별, 분모 24). unseal 뒤에는 둘 다 gold와 같은 비율(`pair_correct_consistency`)을 보조로 낸다 |
| flip rate | 변형(order-rev, para)의 결정이 rep1과 다른 비율(엔진·질문·변형별, 분모 24). 무효는 None 결정으로 비교한다. 변형은 반복이 아니므로 rep2와 합치지 않는다 |
| 지연 | 패널: runner 단조 시계로 dispatch부터 완료까지(pacing 대기 제외). E2E: `duration_ms`/1000이며 ≤0이면 null. 1차는 쌍대 중앙값 차 |
| Score 보조 | regret = best 등급 − 선택 등급. 무작위 best 적중 기준 = \|best\|/w. 첫 후보 기준 = c0 ∈ best. 독립 oracle의 수용 기준을 별도 동결: pool-random@1 = 풀별 수용 후보 비율의 평균, oracle-coverage@4 = 수용 후보 ≥1인 풀 비율, selected success = 선택 후보의 수용 성공률. gap closed = (selected − pool-random@1)/(oracle-coverage@4 − pool-random@1), 분모 0이면 not-measurable. 후보 폭 w=4는 IID 반복 N=4가 아니다. 비변별 풀 = 모든 후보 동급 |
| 비용·사용량 | 03 §5의 세 열을 섞지 않는다. 누락은 null이고 부분합은 `*_observed_sum`, `missing_calls`로 적는다 |
| cascade(τ) | Jev가 유효하고 q ≥ τ면 Jev 결정, 아니면 Astra 결정(Astra가 무효면 오답). coverage = Jev 수락 비율. Jev 실패 뒤 Astra가 낸 결정은 Jev 수락으로 세지 않는다 |

### 3.3 구간
- **source-cluster 부트스트랩.** 관측 클러스터 수만큼 복원추출하고, 두 엔진과 모든 변형을 함께 이동시킨다(쌍대). 2,000회, 백분위 95%.
- **시드.** `int(sha256(split_manifest_sha256∥metric_name)[:16], 16)`.
- **대상.** 1차 지표, AUROC(엔진별과 차이), Brier·ECE 차이, cascade와 fallback의 정확도 차, Score top-1 차, 지연 중앙값 차.
- **E2E.** 클러스터가 10개 미만이면 구간을 내지 않는다. U7(12 task)은 "소표본"이라고 표시하고 보조로만 둔다.

### 3.4 판정(analysis `decision`)
모든 단위는 `outcome=diagnostic-only`다. 인프라 무효가 선택되면 `invalidated`와 `not-measurable`로 적는다.

| 단위 | supported | not-supported | mixed |
|---|---|---|---|
| U0a–U0f | 해당 admission 기준을 모두 통과(§4.3) | 하나라도 미달 → 수정 후 새 lineage | — |
| U1c/U1n | — | — | 항상 mixed. selection은 τ·T 적합에만 쓴다 |
| U2c | CI 하한 > −0.05 ∧ Jev AUROC CI 하한 > 0.5 | CI 상한 < −0.05 | 그 외 |
| U2n | CI 하한 > −0.05 | CI 상한 < −0.05 | 그 외 |
| cascade(U2c 보조) | 동결 τ의 test 정확도 ≥ fallback − 0.02(점추정). CI 하한이 −0.02 아래면 '불확실'로 표기 | τ 없음 또는 −0.02 미달 | — |
| U3 | CI 상한 < 0초(Jev가 더 빠름) | CI 하한 > 0초 | 그 외 |
| U4 | CI 하한 > −0.10 | CI 상한 < −0.10 | 그 외 |
| U6a | CI 하한 > −0.05 | CI 상한 < −0.05 | 그 외 |
| U2s, U5p/U5s, U6b, U7, U8 | — | — | 기술통계만 보고하므로 mixed |
| X1(v2.2) | CI 하한 > −0.05 ∧ Jev의 P(supported) AUROC CI 하한 > 0.5 | CI 상한 < −0.05 | 그 외 |
| X2(v2.2) | CI 하한 > −0.10 | CI 상한 < −0.10 | 그 외 |

- 1차 지표는 단위당 하나다. 보조 지표는 서술용이며 추가 검정을 하지 않는다.
- 층은 따로 보고한다: 봉투 안·밖, (c,m) 칸, 언어, no-match, 후보 수.
- test gold는 U2c·U2n·U2s·U3의 attempt가 모두 끝난 뒤에만 연다.

### 3.5 반복 신뢰도 보조 분석(v1)

정의·1차 출처·코드 핀은 [06](06-reliability-lens.md)을 따른다. 과제 i의 독립 전체 시행 N_i개 중 strict 성공 c_i개라면, n ≤ N_i에서:

- `pass@n = mean_i[1 − C(N_i−c_i,n)/C(N_i,n)]`: n회 중 하나 이상 성공.
- `pass^n = mean_i[C(c_i,n)/C(N_i,n)]`: n회 모두 성공.
- C(a,b)는 a<b이면 0. 과제별 계산 후 같은 가중치로 평균한다. 전체 성공률의 n제곱으로 대체하지 않는다.
- U7r0/r1의 같은 12과제·arm·정책·reset·소스 revision을 묶어 n=1,2만 보고한다. A/B 각각 24시행, 총 48시행은 기존 계획 그대로다. C는 §6의 별도 게이트를 유지한다.
- 같은 과제의 Reflection·재판정·repair는 한 시행 내부다. 서로 다른 주입 결함(U8), 후보 4개(U4/U5), 질문 변형(U2s)을 독립 반복으로 세지 않는다.
- U6b는 과제당 1회라 pass@1만 가능하다. 의도 분류의 pass^2는 **not-measurable: 반복 부족**이다. U2s의 동일 질문 rep1/rep2와 순서/표현 변형은 분리한다.
- 예정 행렬에 미실행·인프라 무효·증거 누락이 있으면 예정 집계는 not-measurable이다. valid/failed는 실패에 포함한다. replacement는 같은 시행의 lineage이며 N을 늘리지 않는다.
- `n, planned_tasks, complete_tasks, incomplete_tasks, expected_repetitions, observed_repetitions, valid_repetitions, run_spec_sha256s`와 원천 행 포인터를 기존 analysis의 보조 지표에 기록한다. 비용은 실패를 포함한 모든 시행의 합이다.
- 동일 조건의 작은 반복에서 관측한 일관성으로 해석한다. 주지표·승격 조건·모델·effort·quota는 바꾸지 않으며 추가 검정도 하지 않는다. G-3에는 06 §7의 합성·경계·불완전 행렬 검사를 포함한다.

### 3.6 지연 해석(v2)
- **1차 해석은 쌍 내부 비교다.**
  - E2E: 같은 슬롯에서 동시에 실행된 A와 B의 차이. `e2e_pairs`의 `judge_latency_s_delta`와 `runtime_s_delta`를 쓴다.
  - U3: 같은 상태를 A와 B에 동시에 보낸 호출 쌍의 차이. 1차 지표 `paired_median_latency_delta_s`다.
- `pair_sync=false`인 E2E 쌍은 쌍 내부 지연 요약에서 빼고, 그 수와 결과를 따로 보고한다. 성공·복구·비용 분석에는 그대로 포함한다.
- (v2.2 보완 3) U3에서 시간 초과 뒤 대체된 쌍은 지연 요약에서 빠진다. 결과를 서술할 때 제외된 쌍의 수를 함께 적는다.
- **기술통계로만 보는 것.** 시각이 다른 호출끼리 비교, 단위 사이 비교, 이전 cohort(M4 등)와의 비교. 공유 계정(§1.4) 때문에 결론의 근거로 쓰지 않는다.
- E2E 전체 시간에는 root와 cognitive 변동이 섞인다. 판정 호출 지연의 주장 근거는 U3와 E2E 쌍 내부 차이다.
- 영상과 결과 문서에서는 "같은 시각, 같은 계정, 외부 사용 unknown"이라는 조건을 함께 적는다.

### 3.7 분석 연결과 동결 기록(v2.2, 통합 GAP 가운데 Run 몫)
통합 담당 README §5가 Run 몫으로 넘긴 항목이다. 단위 동결 절차(패킷 README (역사적 참조: `run-packets/README.md`; 해당 자료는 이 공개본에 포함되지 않음))에 그대로 넣었다.

1. **`score_tolerance` 동결(GAP 4).**
   - U0b는 규칙 상한인 `score_tolerance=0.05`로 돌린다. 편차는 원문을 느슨하게 파싱해 따로 잰다.
   - U0b가 끝나면 U0b 요약의 `score_expectation`(`orders_measured`, `max_abs_deviation`, `tolerance`)에서 §4.1 규칙 값을 읽는다. 그 값과 U0b attempts·analysis의 sha256을 `score-tolerance-freeze.json`에 쓴다.
   - U4·U5s·X2의 Jev selector에는 `sum_tolerance=0.025`와 이 동결값을 **명시 인자로** 넘긴다. 코드 기본값은 둘 다 엄격 1e-5라서, 빠뜨리면 조용히 엄격 기준이 적용된다.
   - 시작 전에 selector의 `tolerances`가 동결값과 같은지 모델 호출 없이 확인하고, 다르면 시작하지 않는다. 같은 값이 모든 기록과 receipt에 남는다. run-spec `analysis_plan`에는 동결 파일의 sha256을 적는다.
   - 동결값이 U0b 관측 최댓값 이상이므로, U0b에서 0.05로 받아들인 출력은 동결값으로도 받아들여진다. 관측 최댓값이 0.05 이상인 경우는 예외다.
2. **반복 신뢰도 evidence는 U7r1에만(GAP 5).**
   - `reliability_metric_rows` 행과 `tables/reliability_summary.json` evidence ref(kind `other`)는 U7r1 analysis에만 넣는다. evidence 경로가 phase 디렉터리 안에 있어야 하기 때문이다. U7r0 analysis에는 넣지 않는다.
   - 집계 대상은 U7r0과 U7r1 행렬 전체다(§3.5). 둘 중 하나라도 불완전하면 not-measurable이다.
3. **U2s → `stability_summary` 연결(GAP 5). v2.2 보완: 통합 0019·0022가 구현했다.**
   - 입력: 두 primitive의 `attempts.jsonl`에서 `selected_for_analysis=true`인 행과 그 native-result receipt(`receipts/<attempt_id>.json`).
   - 키: (engine, primitive, state_id). 변형 값은 receipt의 `variant`(rep1, rep2, order-rev, para)다.
   - 결정 값: `status=admitted`이면 Choice는 native-result의 `receipt.verdict`, Noul은 `receipt.boolean_projection`의 정규 JSON(키 정렬)이다. 그 밖의 경우(검증기 거부, 선택된 무효)는 None이다.
   - gold는 unseal 뒤에만 같은 표현으로 붙인다.
   - (engine, primitive)마다 24개 항목을 `decision_metrics.stability_summary`에 넣는다. 변형이 하나라도 빠진 상태가 있으면 U2s primary는 not-measurable이다. 채워 넣지 않는다.
   - 구현: `verdict_panel_runner.stability_report`와 CLI `stability`(0019). 0022에서 run별 primary 블록(`runs.<primitive>.primary`)으로 바꿨다. Choice run은 `jev_choice_pair_consistency`, Noul run은 `jev_noul_pair_consistency`이고 분모는 계획 상태 수 24다.
   - 그래서 U2s는 U1·U2처럼 run-spec 두 개(U2s-c, U2s-n)로 동결한다. `PanelUnit` 하나가 두 run을 함께 쓰기 때문이다. 같은 이유로 U0a도 두 개(U0a-c, U0a-n)로 나눴다.
   - 그 run에 선택된 무효가 있거나 변형이 빠지면 primary는 not-measurable이다.
4. **freeze 셀 필드(GAP 2).** E2E 단위의 `freeze.json` 셀마다 `policy_digest`, `reset_digest`, `case_sha256`, `task_checksum`, `verifier_sha256`을 적는다.
   - 정본은 셀 필드다. receipt의 같은 이름은 셀에 없을 때만 쓴다(03 §5.1).
   - 빠지면 반복 집계는 `contract_mismatch`이고 새 열은 null이다.
5. **private receipt 경로(GAP 2).** `<phase>/private-receipts/<attempt_id>.json`에 둔다. 권한은 0600이고 분류는 withheld-private다.
6. **열 이름.** 정본 6개만 쓴다(§2.4).
7. **U3 분석 기록(v2.2 보완 3, 통합 0025).**
   - CLI: `python -m evals.benchmarks.verdict_panel_runner latency --run-spec U3 --run-dir (Choice run 디렉터리) --split-manifest heldout-public/split-manifest.json [--gold … --aliases …] --record`.
   - seed는 공개 test manifest 파일의 sha256이다. analysis의 `decision.hypothesis_status`는 보고서의 `primary.decision`이다.
   - `--record`는 산출물을 배타 생성하므로 한 번만 쓸 수 있다. gold 보조 정확도까지 넣으려면 unseal 뒤에 한 번에 기록한다. 1차 지연 지표는 gold 없이도 정해진다.

## 4. 무효·중단 규칙

### 4.1 무효 분류

| 분류 | 예 | attempt | 정확도 | 확률 지표 | 단위 영향 |
|---|---|---|---|---|---|
| 판정 출력 무효 | 스키마·라벨·유한성 위반, 합 허용 초과, argmax 불일치, Score 기대값 허용 초과, 거부, 예상치 못한 stop_reason, Score `judge_error` fallback | valid / failed (`invalid_judge_output`) | 오답 | 제외(분모 기록) | 계속 |
| 인프라 무효 | 응답 없는 전송 실패·시간 초과, 일시적 429(v2.2 보완 4), 캡처·receipt 누락, harness 오류, 한도 소진, 관찰 체크 실패 | invalid / unknown | — | — | 패널·Score-S는 아래 분류표와 §4.2, E2E는 중단 |
| 경로 위반 | Astra PAYG, 모델·effort·provider 불일치, 전역 Jev | invalid / unknown | — | — | 즉시 중단, 수정 후 새 lineage |
| Jev의 LLM fallback | Jev 실패 뒤 Astra가 결정한 모든 경로 | Jev 결정으로 보면 failed | Jev 오답 | — | 계속(cascade 수락으로 세지 않음) |
| 사용량 unknown | 토큰·캐시·추론 누락 | 영향 없음 | — | — | null로 두고 0으로 바꾸지 않음 |

**호출 실패 분류(패널 runner·Score-S, 통합 0027·0028, v2.2 보완 4).** 분류 함수는 `verdict_panel_runner.call_failure_class` 하나이고 Score-S도 같은 표를 쓴다. E2E(Harbor) runner의 분류는 바꾸지 않는다(대체 없음).

| 예외·HTTP 코드 | 분류(`failure_class`) | 처리 |
|---|---|---|
| 호출 시간 초과(Astra 180초, Jev 60초), `httpx.TransportError`, OpenAI SDK 연결·시간 초과, HTTP 408·5xx | `transport_error` | §4.2: 비선택으로 보존하고 같은 입력으로 정확히 1회 대체 |
| **일시적 429**(아래 한도·과금 코드가 없는 rate limit, 0028) | `rate_limited` | `Retry-After`의 초 값 또는 HTTP-date까지의 대기를 0–120초로 제한한다. 없거나 해석 불가·비유한 값이면 30초. 이후 §4.2로 정확히 1회 대체 |
| 한도·과금: `BillingError`·billing-fatal SDK 오류, HTTP 402, 429의 provider code/type에 `quota`·`billing`·`usage_limit`·`usage_not_included`·`plan_limit` 포함 | `quota_exhausted` | 대체 없이 즉시 중단, 인프라 무효(§4.3) |
| HTTP 401, 403 | `harness_error` | 대체 없이 중단 |
| HTTP 400과 그 밖의 4xx, 그 밖의 예외, 모델 호출이 없는 Score-S `judge_error` | `harness_error` | 대체 없이 중단 |
| 응답은 왔지만 계약 위반(스키마, 라벨, 확률 합, argmax, 거부, stop_reason, Score 기준 변경, listwise 범위 밖 index) | 판정 출력 무효 | valid, 오답, 계속(§3.1) |
| 응답 모델·provider가 route와 다름(패널) | `route_violation` | 즉시 중단 |

- 일시적 429를 대체하는 이유: 공유 계정(§1.4)과 동시성 4에서는 일시적 429가 날 수 있다. 그때마다 단위가 무효가 되면 재실행 비용이 크다. 대체율 2% 상한과 대체 실패 시 중단은 그대로다.
- 이 표는 #2 고정(0028 포함)을 쓰는 단위에 적용된다. #1 고정의 0027 표에서는 모든 429가 `quota_exhausted`다. E 단위는 이 표를 쓰지 않는다.

- 1차 분석은 고정 SHA의 파서 판정을 그대로 따른다. I-패널 U0c-i·U6a의 Jev Choice 확률 합 허용치는 엄격 1e-5다. 완료 판정 패널의 0.025와 구별한다. 반대 허용치로 raw answer를 다시 파싱한 분류(엄격 1e-5 / 완화)는 보조 지표다.
- **Score 기대값 허용치** = min(0.05, max(0.03, U0b에서 관측된 |score − Σ i·p_i| 최댓값을 0.01 단위로 올림)). U0b 뒤 동결하고, 이후에는 바꾸지 않는다.
  - (v2.2) U0b 자체는 상한 0.05로 돌린다. 동결값은 `score-tolerance-freeze.json`에 적고, U4·U5s·X2의 Jev selector에 명시 인자로 넘긴다(§3.7-1).

### 4.2 패널 전송 오류(사전 등록 예외, 패널 단위에만 적용)
- 응답이 없는 전송 실패는 invalid로 보존하고 `selected_for_analysis=false`로 둔다. 같은 입력으로 child attempt를 **정확히 1회** 대체한다(`parent_attempt_id`).
- 대체도 실패하면 그 대체 attempt를 선택된 invalid로 남긴다. 이 경우 primary는 not-measurable이고 단위를 중단한다.
- 대체 수 / 계획 호출 수가 0.02를 넘으면 즉시 중단한다.
- (v2.2 보완 5) `rate_limited`인 비quota 429도 이 경로로 대체한다. 대체 전 `Retry-After` 초 값 또는 HTTP-date를 읽고 0–120초로 제한한다. 없거나 해석 불가·비유한 값이면 30초다. 기다린 시간은 실패 attempt의 `retry_wait_s`에 기록하며 모든 지연 지표에서 제외한다.
- 대체는 같은 항목을 채우는 것이므로 분모는 줄지 않는다. E2E에는 대체가 없다(03 §4 규칙).
- (v2.2 보완 3) Score-S 선택 단위(U0b·U4·U5s·X2)에도 같은 규칙을 쓴다(통합 0024). 응답 없는 전송 실패는 1회 대체하고, 대체율이 2%를 넘으면 중단한다. 응답이 계약을 어기면 §3.1의 오답이다.

### 4.3 중단 규칙

| 조건 | 조치 |
|---|---|
| 경로 위반, 비밀값 노출 | 즉시 중단 → 조율자에게 보고. 노출은 사용자 확인 후 처리 |
| 계정 지문·plan 변경, 만료 여유 부족 | 시작하지 않거나 중단(§1.2) |
| 단위 Astra 상한(`budget.limit`), Jev 원장(§9) | 새 호출 금지. 진행 중이면 중단하고 not-measurable. v2에서 창 상한 1,300은 폐지했다 |
| quota: 투영 종료 사용률 > 90% | 시작하지 않고 멈춘다 → 조율자가 사용자에게 초기화 요청 → 새 G0 기록과 지문 확인 → 같은 단위 시작(§7). 순서는 바꾸지 않는다 |
| quota: 진행 중 사용률 ≥95% 또는 한도 오류 | 중단 → 인프라 무효 → 초기화 뒤 새 lineage. 한도 오류는 `quota_exhausted` 분류다(§4.1 분류표: `BillingError`·billing-fatal SDK 오류, 402, quota·billing·usage_limit·usage_not_included·plan_limit 코드의 429). 일시적 429는 여기에 들지 않고 §4.2로 간다 |
| 인증 실패(401, 403) | 중단(`harness_error`). 자격 증명을 확인한 뒤 새 lineage |
| 쌍 시작 skew > 1초(디스패처) | 단위 중단(인프라 무효), 디스패처 수정 뒤 새 lineage |
| 쌍 에이전트 시작 skew > 30초 | 중단하지 않음. `pair_sync=false`로 표시(§2.4, §3.6) |
| 슬롯 한 arm의 인프라 무효 | 형제 arm은 끝까지 보존하고 다음 슬롯은 시작하지 않음(E2E 규칙) |
| 트랙 겹침(잠금 위반) | 나중에 시작한 단위 중단, `schedule_overlap` 인프라 무효(§2.5) |
| admission: 엔진별 판정 무효율 > 10%, 경로·스키마 미승인, 허용 분류 미기록 | 다음 단위로 진행하지 않음 |
| E2E: 첫 인프라 무효 셀 | dispatch 중단(의미적 실패는 계속) |
| 자연 풀: U0b에서 비변별이면 | U5는 서술용으로만 쓴다(중단 아님) |
| playback 승인 부재 | 자연·주입 E2E를 동결하지 않는다. Run 담당은 재생 승인을 스스로 발급할 수 없다 |
| 조율자나 사용자의 중지 지시 | 즉시 중단 |

## 5. τ·온도 선택(selection split에서만)
1. **입력.** U1c·U1n의 유효 출력만 쓴다. test 입력과 gold는 봉인 상태를 유지한다.
2. **온도.** 엔진 × 질문별로 T ∈ {0.25, 0.35, 0.5, 0.7, 1, 1.4, 2, 2.8, 4, 5.6, 8} 중 selection 평균 NLL이 최소인 값을 고른다. 동률이면 1에 가까운 값이다.
   - Choice: softmax(ln p / T), 0확률은 0으로 둔다.
   - Noul: σ(logit(p)/T).
   - 온도는 Brier·NLL·ECE의 보조 보고에만 쓴다. AUROC와 cascade는 원시 q를 쓴다.
3. **τ.** 격자 {0.50, 0.55, …, 0.95, 0.975, 0.99, 1.00}. Choice cascade에서 selection 정확도 ≥ fallback(Astra) − 0.02를 만족하면서 coverage가 최대인 τ를 고른다.
   - coverage가 같으면 큰 τ를 고른다.
   - 첫 단계 출력이 무효면 항상 fallback으로 넘긴다.
   - 만족하는 τ가 1.00(coverage 0)뿐이면 "허용 τ 없음"이다.
4. **동결.** T, τ, selection 지표, U1 attempts·analysis의 sha256을 담아 `selection-freeze.json`을 쓴다. 그 sha256을 U2c·U2n의 `analysis_plan`에 적고 나서야 첫 test 호출을 한다. 이후에는 재적합하지 않는다.
5. **(v2.2 보완 5) 외부 검증.** X1은 이 파일의 T와 τ를 그대로 쓰며, 파일의 sha256을 analysis_plan에 묶는다. 허용 τ가 없어 null이면 τ 의존 선택적 위험·coverage·cascade는 not-measurable이고, 원시 이진 정확도·AUROC는 별도로 계산한다. T가 없으면 해당 보정 지표만 not-measurable이다. 외부 데이터로 T·τ·임계값을 다시 고르지 않는다(§11).

## 6. arm C 승인 조건
다음을 모두 충족할 때만 U0f를 거쳐 U7에 C를 넣는다. 하나라도 빠지면 run-log에 "C 미실행(사유)"로 남긴다.
1. §5에서 허용 τ가 나왔다.
2. U2c test split의 오프라인 cascade 정확도가 fallback − 0.02 이상이다(점추정).
3. 고정 SHA에 arm C 코드가 있고, 그 코드의 checker 판정-호출 매핑 테스트가 통과했다.
4. U0f 2셀이 통과했다.
5. C 몫(약 +100 Astra)을 포함한 U7 투영이 §7의 90% 규칙을 통과한다. 필요하면 초기화한 뒤 통과시킨다. v2에서 창 조건을 대체했다.

C를 넣으면 U7의 각 반복은 12 task × {A, B, C} = 36 롤아웃이 되고, 슬롯마다 세 trial이 동시에 실행된다(§2.4, 모델 없는 3컨테이너 점검 선행). C는 U2c의 동결 τ를 그대로 쓴다. C 결정에는 test gold가 필요하므로 U2c·U2n·U2s·U3가 끝나고 unseal한 뒤에만 내릴 수 있다(§3.4).

## 7. quota 투영(v2 재작성)
v2 원칙: **quota는 일정 제약이 아니다.** 사용자에게 주간 한도 초기화권이 있다. 단위를 quota 때문에 미루거나, 줄이거나, 다음 창으로 넘기지 않는다. 설계 순서(선행 의존)와 병렬 스케줄(§2.5)만 따른다. 이 절의 목적은 **단위 도중 한도 소진(인프라 무효)을 막는 것** 하나다. 운영 절차와 원장 템플릿은 run-packets/quota/ (역사적 참조: `run-packets/quota/README.md`; 해당 자료는 이 공개본에 포함되지 않음)에 있다.

- **G0(기록 완료, 22:16 KST).**
  - fp `57faa696f3a8`, plan `prolite`.
  - 주간 창(primary) 1개: 604,800초, used 51%, reset 2026-10-01 04:10 KST, allowed=true.
  - 5시간 창은 없다. 따라서 v1의 5시간 창 규칙(계획 일시정지, U3의 5시간 창 조건)은 적용하지 않는다. 이후 스냅샷에 짧은 창이 나타나면 같은 투영을 창별로 적용하고 run-log에 적는다.
- **방법.** Codex `/status`를 보거나, 사용자 승인 경로로 WHAM usage를 1회 조회한다. 토큰과 auth 파일은 출력하지도 해시하지도 않는다.
- **보정 계수 r.** U0가 끝나면 다시 기록하고 r = Σ Δused% / Σ(프로그램 Astra 호출/100)를 계산한다.
  - 누적 비율로 계산하고 단위마다 갱신한다.
  - 영상 세션의 외부 사용이 섞이므로 빼지 않는다. 그래서 보수적인 값이 된다.
  - U0 구간 Δ가 2포인트 미만이면 해상도를 반영해 (Δ+1)/(호출/100)을 잠정값으로 쓴다.
- **시작 규칙.** 각 단위 시작 직전에 `projected_end = used_now + r × 계획 Astra 호출/100`을 계산한다.
  - 90% 이하면 시작한다.
  - 90%를 넘으면 **시작하지 않고 멈춘다.** 조율자가 사용자에게 초기화를 요청한다. 초기화 뒤 새 G0를 기록하고 지문을 확인한 다음, 같은 단위를 시작한다.
- **초기화 이벤트 기록.** run-log와 private receipt에 적는다: 전후 used%, reset 시각, 계정 지문 앞자리, plan. 지문이 `57faa696f3a8`이 아니면 계정이 바뀐 것이므로 중단하고 보고한다(§1.2).
- **총량(v2.2 보완).** 계획 Astra 호출은 약 3,641회다(X1a 2, X1 239, X2 960 포함, C 포함 시 약 +100). 외부 단위의 Astra 입력은 X1 약 1.22M, X2 약 0.70M 토큰이다(o200k 추정). 총량은 참고값이고 시작 여부는 단위마다 위 규칙으로 정한다.
- **단위 도중.** Astra 300호출이 넘는 단위(U4, X2)는 300호출마다 확인하고, U5p는 중간에 1회 확인한다. 95% 이상이거나 한도 오류가 나면 중단하고 인프라 무효로 처리한 뒤, 초기화하고 새 lineage로 간다(§4.3).
- **기록.** 모든 단위의 시작 직전·종료 직후 used%를 원장과 run-log에 적는다.
- **참고용 우선순위.** 결과 가치 순서는 [스케줄](schedule.md) §4에 있다. 판단 참고용이며 축소나 연기의 근거로 쓰지 않는다.
- v1의 "여유의 80%" 규칙, 창 배치(W1/W2), 창당 1,200호출 fallback, 창 상한 1,300은 v2에서 폐지했다.

## 8. Replay 쌍과 순서(결과를 보기 전에 고정)
1. **순서와 선정 규칙.** v2.1에서 구현에 맞췄다. 계산은 `run-packets/tools/make_packet.py`가 한다.
   - **dispatch 순서**(U1, U2, U2s, U3): `verdict_panel.ordered_workload_ids(ids, split_manifest_sha256)`, 즉 `sha256(id + manifest sha256)` 오름차순이다. manifest sha256은 그 split의 공개 manifest 파일 바이트의 sha256이다(test는 재빌드본 `9fc1e80d…`, §2.3).
     - 그다음 **quad 간격 규칙**을 적용한다: 같은 quad의 상태가 연속 4자리(동시성 창) 안에 둘 이상 들어가지 않도록 해시 순서를 유지한 채 결정론적으로 뒤로 미룬다.
     - (v2.2 정정) 각 자리에는 해시 순서에서 가장 앞선 상태 가운데, 최근 3자리에 같은 quad가 없는 상태를 놓는다. 이 선택이 막다른 곳으로 이어지면 되돌아가서 해시 순서의 다음 상태를 시도한다.
     - 결과는 규칙을 만족하는 배열 가운데 해시 순서 기준으로 사전식 첫 번째다. 되돌아갈 일이 없으면 v2.1의 뒤로 미루기와 결과가 같다. 유효 배열이 없으면 생성기가 멈추고 위반을 내보내지 않는다.
     - 재빌드 manifest로 생성한 결과는 다음과 같다. U1·U2·U3는 v2.1 방식과 같은 순서이고 위반이 0건이다. U2s에서는 v2.1 방식이 마지막(24번째) 자리에서 위반 1건을 냈다. 되돌아가기 뒤에는 20번째 자리부터 순서가 달라졌고 위반은 0건이다.
   - **U2s·U3 부분집합**: 봉인 쪽에서 **`sha256(원래 state_id ∥ test gold_sha256)` 오름차순**으로 칸마다 층화해 뽑았다(U2s 칸당 6, U3 칸당 30이며 U3가 U2s를 포함).
     - 공개 목록은 별칭 ID만 담는다(`subsets.test.json` sha256 `63de618a…`, 선정 규칙 sha256 `35ad8106…`).
     - 별칭을 다시 만들어도 뽑힌 상태는 같고 공개 목록의 별칭만 바뀐다. v1의 "`sha256(id∥split_manifest_sha256)`로 층화"는 이 규칙으로 대체한다.
   - **클러스터 단위 선정**(Score 자연 과제, E2E admission): 그 split의 `gold_sha256`을 salt로 한 `sha256(cluster_id + gold_sha256)` 오름차순이다.
     - selection 1–12번은 U5p, 13번은 U0b, 14–15번은 E2E admission이다.
   - **E2E 원천**(v2.2, 옵션 E): `sha256(source_id + salt)` 오름차순이다. salt는 원천 20개 digest를 정렬해 이은 문자열의 sha256이다. 1–12위는 U7, 13–18위는 U8, 19–20위는 예비다(§2.3).
   - **통제 풀**(U4·U0b): quad 90개를 `sha256(pool_id + selection gold_sha256 + test gold_sha256)` 순서로 정렬한다. 앞 80개는 U4, 81–82번은 U0b다.
   - **I-패널 가족**(U6a): `sha256(family_id + analysis 파일 sha256)` 오름차순이다.
2. **Replay 쌍.** U7·U8의 과제명은 옵션 E 공개 목록(`e2e-sources.json`)이 도착하면 확정된다(§2.3). 규칙은 지금 고정한다: U7은 자연 1위 원천의 rep0, U8은 주입 1위(전체 13위) 원천의 c1m1 슬롯이다. 순위는 저작이 끝난 뒤 digest로 정해지므로, 내용이나 결과를 보고 고를 수 없다.

| 단위 | Replay 쌍 | 배치 |
|---|---|---|
| U7r0 | 자연 1위 원천 `e2e-golfballs`, rep0(U7r0-s01) | A 왼쪽 · B 오른쪽(C는 부록) |
| U8c | 주입 1위 원천 `e2e-telescopes` c1m1(U8c-s03) | A-Choice 왼쪽 · B-Choice 오른쪽 |
| U8n | 주입 1위 원천 `e2e-telescopes` c1m1(U8n-s03) | A-Noul 왼쪽 · B-Noul 오른쪽 |
| U6b | `inbox-korean` rep0: U6b-s03 | 준비된 프로토콜 그대로 |
| 패널·Score | 없음 | receipt로만 설명 |

v2부터 Replay 쌍은 같은 슬롯에서 동시에 실행된 두 trial이다. 화면의 두 벽시계는 실제 같은 시간대를 가리킨다. 좌우 배치는 실행 순서와 무관하게 고정한다(§2.4).

3. 선정된 쌍이 무효이거나 불완전해도 바꾸지 않는다. "영상 부재"로 보고하고, 모든 쌍을 manifest에 보존한다(`replay_preselected=true`).
4. admission의 재생 확인(`playback-check.json`)은 사람 검토자가 발급한다. Run 담당이 할 일은 cast와 MP4를 준비하고 조율자에게 요청하는 것까지다.

## 9. Jev $1 상한
- 프로그램 전체에 host 수준 원장을 하나 둔다. 각 호출의 추정액은 `input_tokens × $0.042/1e6`이다(출력 $0, `output_tokens`는 보존).
- 입력 토큰이 없으면 호출당 25,000 토큰(약 $0.00105)을 **예약 열**에 따로 적는다.
- 단위 시작 전에 다음을 확인한다: 누적(추정 + 예약) + 단위 투영(Jev 호출 수 × 앞선 단위들의 p95 입력 토큰 × 단가)이 $0.90 이하여야 한다.
- 진행 중 누적이 $0.95 이상이 되면 즉시 중단한다.
- 예상 총액은 약 $0.17이다. 실제 청구는 TypeSafe가 보고할 때까지 unknown이다.
- (v2.2) $0.17은 X1·X2를 넣기 전의 값이다. o200k 추정으로 X1은 약 $0.038(입력 907,232 토큰), X2는 약 $0.015(352,538 토큰), X1a는 $0.002 미만이다. 합계 투영은 약 $0.22다. 실제 Jev 토크나이저 값은 다를 수 있다.
- 사용량이 모두 빠질 때의 예약 열(호출당 25,000 토큰)은 X1 $0.251, X2 $0.504다. X2 시작 전에 누적(추정 + 예약) + X2 투영이 $0.90을 넘지 않는지 먼저 본다. $0.90 시작 규칙과 $0.95 중단 규칙은 그대로다.

## 10. 기록과 보고
- **run-log.** `run-log.md`에 append-only로 적는다. 형식은 `시각(KST) | Run | SHA | 단위·이벤트 | 결과`이며 이벤트는 freeze, start, pause, stop, complete, not-run이다. 결과 칸에는 다음을 적는다: Astra·Jev 호출 수, 입력·출력 토큰(unknown 개수 포함), used% 전후, valid·invalid·대체 수, primary 값 또는 not-measurable, 계정 지문 앞자리. 잘못 적은 줄은 고치지 않고 정정 줄을 덧붙인다.
- **조율자 보고(단위 종료 시).** 5줄 이내로 쓴다: run_id, 계획 대비 실행 수, 무효·중단 사유, primary와 판정 상태, 다음 단위의 quota 투영.
- **v2 추가 기록.**
  - quota 스냅샷과 초기화 이벤트(전후 used%, reset, 지문 앞자리, plan).
  - E 단위의 슬롯 요약: 슬롯 수, `pair_sync=false` 수, 최대 에이전트 시작 skew.
  - 트랙 전환 시각.
  - 재생 검토 요청·승인 시각.
- **데이터 담당 인계.** run 디렉터리 경로, `contract.py validate-run-bundle` 결과, attempts·results·analysis의 sha256, 봉인 해제 여부. 테이블(`call_ledger`, `judge_items`, `noul_items`, `e2e_trials`, `e2e_pairs`, `primitive_summary`)은 데이터 담당이 receipt에서 만든다.
- **금지.** PR 병합, release, tag, jev automation 재활성, private-secrets 열람.

## 11. 외부 검증(X1a·X1·X2, v2.2, 사용자 결정)

외부 데이터 담당이 `external/{cuavb,m2w}/`의 변환과 자체 검사를 마쳤다. 이 절은 데이터 담당의 보완 초안(`external/05-s11-external-draft.md`)을 병합하고 조율자 결정(§0-9–13)을 반영한 것이다.
- X1의 코드 구성은 0025(Choice 단독 `PanelUnit`)·0026(이진 채점)·0030(보존 attempt 연결·CLI·서술 지표)다. 고정 #2 후보에 모두 들어 있다. X1a 통과와 `selection-freeze.json`의 T·τ 동결 기록이 없으면 X1을 동결하지 않는다.
- X2는 `score-tolerance-freeze.json`과 통합 패치 0024(Score-S 제한 동시 실행)가 필요하다.

### 11.1 목적과 위치
- 질문: 우리가 저작한 패널(M7, Score 통제 풀)에서 본 Jev와 Astra의 차이가, 남이 만든 과제와 사람 라벨에서도 같은 방향으로 나타나는가.
- 외부 타당도 점검이다. U2c·U4의 결론을 대체하거나 뒤집지 않는다. 결과는 별도 층으로 보고한다.
- 동결값만 쓴다. T·τ는 `selection-freeze.json`, Score 허용치는 `score-tolerance-freeze.json`에서 오고, 프롬프트·스키마·코드는 고정 SHA 그대로다.

### 11.2 데이터와 변환(외부 데이터 담당)

| 항목 | X1 | X2 |
|---|---|---|
| 원천 | `microsoft/CUAVerifierBench` revision `c19eb323…`, MIT | `osunlp/Mind2Web` revision `17ece8eb…`, `test.zip` sha256 `8f5fbe72…`. 데이터는 CC BY 4.0이고, 공식 README가 압축 푼 파일의 온라인 재배포를 금지한다 |
| 단위 | 궤적 1개 = Choice 상태 1개 | action step 1개 = 후보 4개 풀 1개(과제당 최대 1 step) |
| 선택 | 표집 없음. 사람 라벨 동률만 뺀다 | split마다 80개. 키 `sha256(annotation_id ␟ action_uid ␟ salt)` 오름차순이고, salt는 압축을 열기 전에 고정했다 |
| 규모 | **239** = 궤적 260 − 동률 21(모두 om2w의 2인 1:1). internal 154, om2w 85 | **240** = test_task, test_website, test_domain 각 80. 훑은 309 step 중 정답 요소 없음 13, 같은 과제 중복 56을 뺐다 |
| 입력 | 지시문, 행동 로그(인자·에이전트 생각·시각·페이지 URL), 최종 답, 시작 URL. 화면 캡처와 도구 결과는 없다 | 과제 문맥(웹사이트, 과제 문장, 목표 step 이전 행동) + 후보 4개(tag, 속성 8종 120자, 텍스트 300자) |
| 정답 | UV-blind 사람 판정의 엄격 다수결. 수용 119, 거부 120 | 기록된 다음 목표 요소 1개(grade 3)와 음성 3개(grade 0). 다른 정답 요소, 정답의 DOM 조상·자손, 표현이 같은 요소는 음성에서 뺀다 |
| 절단 | T1(시작 + 첫 5행동 + 생략 표시 + 들어가는 최대 꼬리, 상태 ≤60,000자). 0건, 최대 59,816자 | 없음. 표현 규칙의 자르기만 있다. 후보 최대 367자 |
| manifest | `03002e70…` | `413fdbcc…` |
| 모델 입력 / 정답 파일 | states `fa5b0266…` / gold `44b57959…` | 공개 풀 `c19669a3…` / pools-graded `dbe4bb45…`, gold `f8fdf01c…` |
| 순서 목록 | `7a5c2052…`(239) | `4c51f589…`(240) |
| 클러스터 | `cluster_id` 133(om2w 웹사이트 63, internal 과제군 70) | 웹사이트 94(test_task 44, test_website 10, test_domain 40) |
| 누설 검사 | 통과: 라벨 필드 0, 자유 문장 일치 0, 원 task ID 0 | 통과: 금지 키 0, 목표·이후 행동 문자열 초과 출현 0 |

- 절단, 풀 구성, 표현 규칙은 모델 출력을 보기 전에 정했고, 두 엔진이 같은 바이트를 받는다. X2의 정답 선택·음성 제외 규칙은 23:42 KST에 확정했다. 그 전에 본 것은 한 샤드의 필드 이름과 정답 플래그 분포뿐이다.
- 정답 파일은 모델 입력과 분리돼 있다. Run 담당은 해당 단위의 attempt가 끝날 때까지 열지 않는다.
- 생성기는 X1 states와 X2 공개 풀의 ID만 읽고, 순서를 `sha256(id + manifest sha256)`으로 다시 계산했다. 두 목록 모두 데이터 담당의 순서 목록과 일치했다.

### 11.3 가설과 1차 지표
- **X1** `x1_binary_verdict_accuracy_delta` = (Jev 이진 정답 − Astra 이진 정답) / 239.
  - 결정 d: 받아들여진 출력이고 verdict가 supported면 수용, 받아들여졌지만 다른 verdict면 거부, 받아들여지지 않았으면 무효다.
  - 정답: d가 무효가 아니고, (d = 수용)이 사람 다수 Correct와 같을 때다. 무효는 오답이다.
  - P(supported)는 receipt의 `probabilities["supported"]`다(유효 출력만). AUROC는 Mann–Whitney이고 동률은 0.5다.
  - 가설: CI 하한 > −0.05이고, Jev의 P(supported) AUROC(사람 성공이 양성) CI 하한 > 0.5.
- **X2** `x2_score_top1_delta` = (Jev top-1 정답 − Astra pointwise top-1 정답) / 240.
  - top-1 정답: 두 순서 점수 평균의 argmax가 grade 3 후보다. 정확한 동률은 가장 작은 `sha256(pool_id␟candidate_id)`로 깬다. 어느 한 순서라도 무효나 fallback이면 오답이다(§3.1).
  - selector 이름은 `astra_pointwise`, `jev_pointwise`, `astra_listwise`다. 1차 값은 `summarize --delta x2=astra_pointwise:jev_pointwise`다.
  - 가설: CI 하한 > −0.10.
- **X1a**(admission, v2.2 보완) `x1_admission_admitted_ratio`(max, 4).
  - 가장 긴 두 상태(`x1-580a8e039ac4aefb` 59,816자, `x1-f2684c4eaf078047` 55,577자)를 두 엔진에 한 번씩 보낸다. Jev 1.13.0의 컨텍스트 한도가 문서에 없기 때문이다.
  - 4호출이 모두 받아들여져야 X1을 동결한다. 실패하면 X1을 동결하지 않고 조율자가 정한다. X1 동결 전에 절단 규칙을 바꾸면 설계 변경으로 기록한다.
  - X1a는 X1 분석 분모에 들어가지 않는다. 두 상태는 X1에서 다시 판정한다.
- 판정은 §3.4 표를 따르고, `outcome=diagnostic-only`다.

### 11.4 보조 지표(서술용, 추가 검정 없음)
- **X1**
  - 엔진별 이진 정확도. 오수용률 = #(수용 ∧ 사람 Incorrect) / 120(무효는 수용이 아니다). 오거부율 = #(수용 아님 ∧ 사람 Correct) / 119(무효 포함).
  - TPR, TNR(무효는 오답), balanced accuracy = (TPR + TNR) / 2.
  - P(supported)의 AUROC·Brier·ECE(등폭 10구간). gold별 세 라벨 분포.
  - 오류 탐지 AUROC(점수 1 − q)와 risk–coverage. q는 receipt의 세 라벨 확률 최댓값이다.
  - 동결 τ의 선택적 위험: 포함 = 유효 ∧ q ≥ τ, coverage = 포함 / 239, risk = 포함 중 이진 오답 / 포함. τ가 없으면 not-measurable이다. 이진 투영 q로 바꾸면 τ의 뜻이 달라지므로 세 라벨 q를 쓴다.
  - 동결 τ의 오프라인 cascade(포함이면 Jev, 아니면 Astra 결정)의 이진 정확도와 coverage, 동결 T를 적용한 보정 지표. 허용 τ가 없어 null이면 cascade·선택적 위험·해당 coverage만 not-measurable이다. T가 없으면 해당 보정 지표만 not-measurable이다. 원시 1차 지표를 이 이유만으로 무효화하지 않는다.
  - **쌍대 불일치(McNemar, 조율자 결정 12)**: b = #(Jev 정답 ∧ Astra 오답), c = #(Jev 오답 ∧ Astra 정답)만 보고한다. p값은 내지 않는다.
  - 참고값(결론에 쓰지 않음): 데이터셋 UV·레거시 검증기와 gold의 일치율(`reference.x1.jsonl`).
  - 층: source split, 검토자 수(1 / 2–3), `<no_answer>` 4건, 상태 길이 사분위.
- **X2**
  - split별 top-1. pool-random@1 = 0.25 대비 gap closed = (top-1 − 0.25) / 0.75. oracle-coverage@4 = 1.0.
  - 첫 후보 기준: forward 위치 0에 정답이 있는 비율 51/240 = 0.2125.
  - 양순서 일관성(두 순서가 모두 유효한 풀에서 forward 승자 = reverse 승자인 비율)과 순위 일치 τ_b.
  - listwise 참조(순서별 적중 평균), 무효·fallback·동률 깨기 수.
  - McNemar b, c(X1과 같은 식, p값 없음).
  - 층: 조작(CLICK 206, TYPE 23, SELECT 11), step 위치, 정답 tag, 정답 표현에 속성·텍스트가 없는 10풀.
- 공통: 사전학습 노출 여부는 unknown이다. 지연은 기록만 한다.

### 11.5 분석
- 구간은 §3.3의 클러스터 부트스트랩(2,000회, 백분위 95%)이다. 두 엔진과 두 순서를 함께 옮긴다.
  - X1 클러스터는 빌더의 `cluster_id` 133개다.
  - X2 클러스터는 웹사이트 94개다. split별 구간은 낸다. 다만 test_website는 클러스터가 10개로 최소 조건(10)에 겨우 걸린다는 점을 함께 적는다.
- seed는 `int(sha256(외부 manifest sha256 ∥ metric_name)[:16], 16)`이다. dispatch 순서는 `sha256(id + manifest sha256)` 오름차순이다(`workload-order.x1.json`, `workload-order.x2.json`).
- X1·X1a는 패널 규칙(동시성 ≤4, 180초, 전송 오류 대체 1회, 대체율 2%, §4.2)을 따른다. 칸은 (llm, choice)와 (jev, choice)다. 0025의 기본 모드(`latin`), `max_concurrency=4`이고, 칸 순서는 상태 순번이 짝수면 A→B, 홀수면 B→A다. run-spec의 comparator와 명령에 적었다.
- X2는 `score_selection.dispatch_selection`이 풀마다 selector별로 forward, reverse를 보낸다.
  - 통합 0024가 제한 동시 실행(≤4, 명시 인자, 산출 바이트 동일)과 호출별 시간 제한을 넣는다. run-spec에는 예고된 값 `max_concurrency=4`, `timeout_seconds=180`(`timeouts={"llm": 180, "jev": 60}`)을 채웠다. 같은 경로를 쓰는 U0b·U4·U5s도 같다.
  - 0024의 제한 동시 실행과 호출별 제한 인자는 고정 #2 후보 소스에서 확인했다. 동결 시 드라이버 호출 인자·해시를 같은 후보에 묶는다.

### 11.6 금지와 고정
- 외부 데이터로 T·τ·임계값·허용치·프롬프트·스키마·절단 규칙을 고르거나 고치지 않는다. 결과를 본 뒤 바꾼 분석은 탐색적이라고 표시하고 결론에 쓰지 않는다.
- 지연 주장은 하지 않는다. 지연의 근거는 U3와 E2E 쌍 내부 비교뿐이다(§3.6).
- 추가로 고정하는 것:
  - X1: `task_contract` 문구(sha256 `b7ddb4cc…`), 행동 로그 매핑, 60,000자 한도와 T1.
  - X2: salt, 선택 순서, 정답·음성 규칙, 표현 틀(`x2-task@1`, 속성 8종, 120/300자).
- 단위 도중 입력이 바뀌면 superseded로 처리하고 새 lineage로 간다.

### 11.7 한계(결과 문서에 적는다)
- **X1 입력에는 화면과 도구 결과가 없다.** 사람은 스크린샷을 봤지만, 모델은 에이전트의 행동·생각·메모만 본다. 판정 기준이 관측으로 뒷받침된 주장을 요구하므로 `insufficient_evidence`가 몰려 오거부가 커질 수 있다. 문턱 없는 P(supported) AUROC를 함께 해석하고, "텍스트 변환본에서의 판정"으로 서술한다.
- X1 에이전트는 Fara-7B 하나다. om2w는 Online-Mind2Web의 편향을, internal은 확인할 수 없는 내부 과제 정의를 가진다. internal 154건은 검토자가 1명이다. 동률 21건을 빼서 애매한 사례가 줄었다.
- X1의 60,000자 한도는 GEODE E2E의 상태 한도다. Jev 1.13.0의 컨텍스트 한도는 확인되지 않았다(X1a로 확인). 가장 긴 상태의 Jev 입력은 약 16,640 토큰(o200k 추정)이다.
- 도메인이 다르다. 우리 패널은 inbox와 주문 도구이고, 외부 데이터는 데스크톱·웹 GUI다. 사람 라벨에도 잡음과 모호함이 있다.
- **X2 후보에는 DOM 맥락이 없다.** tag·속성·텍스트만 보이므로 글자가 같은 다른 요소나 텍스트 없는 아이콘(10풀)을 구분하기 어렵다. 음성은 같은 tag 우선 + 해시로 골랐다. 원 벤치마크(MindAct 상위 50 후보)와 난이도가 다르므로 수치를 비교하지 않는다.
- X2는 step 키 순서로 과제당 1개를 뽑으므로 step이 많은 과제가 더 잘 뽑힌다. 정답 위치는 51/54/78/57로 균등에서 조금 벗어나며(χ² 약 7.5), 양순서로 상쇄한다.
- X2는 step 단위 선택이며, 여러 step 실행의 성공이 아니다.
- Score-S 기록의 수용 규칙 문구는 "rule-oracle verdict supported"로 찍히지만, X2에서는 "기록된 다음 목표 요소"를 뜻한다.
- 공개 데이터셋이므로 두 모델이 사전학습에서 봤는지는 unknown이다. X2 파생 파일에는 Mind2Web 공식 canary 문구를 남겼다.

### 11.8 공개 등급(조율자 결정 11)

| 산출물 | X1 | X2 |
|---|---|---|
| 집계 지표와 구간, revision, 스크립트, manifest·순서·길이 통계 | public | public |
| 항목 ID 목록 | public(`source_task_id`, `excluded.x1.jsonl`) | public(`ids.x2.jsonl`, `excluded.x2.jsonl`) |
| 변환 입력(상태·풀)과 정답 파일 | **reproducible-cache(기본).** MIT라 게시할 수는 있지만, 파생 텍스트 게시는 공개 단계의 개인정보 검토 뒤에 따로 정한다 | reproducible-cache(재배포 금지 조건). 개별 풀의 문맥·후보 텍스트를 인용하지 않는다 |
| 원시 캐시 | reproducible-cache | reproducible-cache |
| 프롬프트, 원시 출력, receipt | withheld-private | withheld-private |

- reproducible-cache는 ID·스크립트·해시·집계만 게시하고, 원본은 각 데이터셋에서 받아 스크립트로 다시 만드는 방식이다.
- CUAVerifierBench(MIT)와 Mind2Web(CC BY 4.0)의 인용과 고지를 적는다. 사람 코멘트 원문은 재배포하지 않는다.

### 11.9 예산과 일정
출처는 `external/cost-estimate.json`이다. 토큰은 tiktoken `o200k_base` 추정이며 Jev 토크나이저와 다를 수 있다.

| 단위 | Astra 계획/상한 | Jev | Astra 입력 토큰 | Jev 입력 토큰 | Jev 추정액 |
|---|---|---|---|---|---|
| X1a | 2/3 | 2 | 가장 긴 두 상태(최대 20,730/호출) | 최대 16,640/호출 | $0.002 미만 |
| X1 | 239/251 | 239 | 1,216,247(호출당 중앙 3,903) | 907,232(중앙 2,892) | $0.038 |
| X2 | 960/1,008(pointwise 480 + listwise 480) | 480 | 698,256(pointwise 500,640 + listwise 197,616) | 352,538(중앙 721) | $0.015 |

- 사용량이 모두 빠질 때의 예약 열은 X1 $0.251, X2 $0.504다(§9). Astra 출력·추론 토큰과 quota 사용률은 추정하지 않았다. X2는 300호출마다 quota를 확인한다(§7).
- 시간(데이터 담당 추정): X1은 동시성 4에서 약 8–47분이다. X2는 순차 실행 기준 약 2.0–12.3시간이다(Astra 호출당 7.2–45초 가정). 0024의 동시성 4가 들어오면 줄어들지만, 실제 시간은 측정 전까지 unknown이다.
- 트랙은 P다. 모두 U2s → U3 → unseal → arm C 결정의 임계 경로보다 앞서지 않는다.
  - X1a: G-1..G-5와 0025 뒤, P 빈 시간. X1 동결 전에 끝나야 한다.
  - X1: X1a 통과, U2c·U2n, `selection-freeze.json`의 T·τ 기록과 해시, 0025·0026·0030 포함 고정 #2 뒤.
  - X2: U2c·U2n, `score-tolerance-freeze.json`, 0024 뒤. 오래 걸리므로 E 트랙이 게이트에 막힌 긴 빈 시간에 둔다.

### 11.10 대기 항목
- **X1 코드 차단 해제**: 고정 #2 후보 `2f2b494d6`에는 0030의 보존 attempt 연결·CLI·서술 지표가 들어 있다. 따라서 초안의 0030 `blocked_by`를 제거한다. 채점 모듈 0026(`external_binary.py`, 1차 `x1_binary_verdict_accuracy_delta`, §11.3 정의)과 Choice 단독 실행 0025도 포함된다. 입력 계약과 채점 정의는 `external/cuavb/README.md` §3·§4에 있다.
  - 남은 동결 조건: 정확한 고정 #2의 G-1..G-5, X1a 4/4 통과, §11.9의 선행 단위, selection에서 만든 `selection-freeze.json`의 T·τ와 sha256 참조다. 코드 차단 해제는 이 조건이나 실행 승인을 대신하지 않는다.
  - 운영 분석은 비공개 `x1_analysis.py`를 진입점으로 쓴다. run-spec에 등록한 진입점 자체의 해시와 `selection-freeze sha256`를 실제 파일과 대조한 뒤, 같은 인자로 고정 `external_binary.main`을 호출한다. 누락·중복·불일치는 gold 읽기 전에 거부한다. 직접 라이브러리 CLI는 이 추가 해시 대조를 하지 않으므로 운영 명령으로 쓰지 않는다.
  - 분석 CLI `python -m evals.benchmarks.external_binary`는 `--selection-freeze`를 필수로 받는다. τ가 null이면 τ 의존 선택적 위험·coverage·cascade를 not-measurable로 두며 외부 데이터에서 다시 고르지 않는다. T가 없으면 해당 보정 지표도 not-measurable이다.
- **I-패널(U0c-i·U6a) 코드 차단 해제**: 0029는 고정 #2 후보에 들어 있으므로 해당 `blocked_by`를 제거한다. intent를 받는 비공개 패널 드라이버와 해시, §2.3의 모드·동시성·엄격 허용치까지 맞춘 뒤에야 단위 동결을 검토한다.
- `blocked_by`는 초안 전용 키다. 코드 차단이 풀린 키의 제거와 단위 동결 조건 통과는 별개다.
- **X2**: 데이터와 run-spec 값을 채웠다. 남은 것은 `score-tolerance-freeze.json`(U0b), Jev selector의 명시 허용치 인자(§3.7-1), 확정 head와 드라이버 인자·해시의 일치 확인이다.
- U3의 Choice 단독 실행과 쌍 동시 지연 모드는 0025로 들어왔다. U3 초안의 `blocked_by`는 지웠다(§1.3-13·16).

## 12. 변경 이력
- v0(2026-09-26): 초안. 조율자 확정 결정을 반영했다. 01·03과 명명·무효 규칙을 맞췄다. Score fallback은 "valid/failed(오답)"로 고정했다(03 §6의 미결 항목을 결정).
- v1(2026-09-26): Anthropic→SPoC/HumanEval/τ-bench 원문·코드 확인 후 §3.5의 pass@n/pass^n 보조 분석 추가. Score의 풀 수용률을 IID pass@4와 구별하도록 §3.2 명칭 교정. 기존 1차 지표·48회 자연 E2E·다른 단위 반복 수·모델·effort·예산은 유지. 실행·봉인 자료 열람 없음.
- v2(2026-09-26 22:1x KST 사용자 결정 반영, Run 담당):
  - 추가: §0 사용자 결정, §1.3의 12–13, §1.4 공유 계정 한계, §2.4 쌍 동시 실행, §2.5 트랙과 비중첩, §2.6 동시 부하 기록, §3.6 지연 해석.
  - 재작성: §7 quota. 초기화권이 있으므로 일정 제약이 아니고, 투영 90% 초과 시 멈추고 초기화를 요청한다. 5시간 창 규칙은 해당 없음.
  - 갱신: §4.3 중단 규칙, §6 조건 5, §8(클러스터 salt, 부분집합 선정, Replay 미리보기), §10.
  - 정정: §2.3의 통제 풀 선정(quad 90개 해시 순서의 앞 80개), Harbor venv 확정(§1.1).
  - 실행 패킷 `run-packets/`를 새로 만들었다.
  - 단위 구성·반복 수·1차 지표·모델·effort·Jev 상한은 그대로다. 모델 호출 0회, 봉인·비밀 폴더 열람 없음.
- v2.1(2026-09-26 23시대, Run 담당, 조율자 요청):
  - 추가: §1.5 설계 누설(m 요인 216/216 복원 가능)과 완화 규칙 4개.
  - §8.1 선정 규칙을 구현에 맞춰 정정했다: U2s·U3 부분집합은 `sha256(원래 state_id ∥ test gold_sha256)`이다. dispatch 순서에 quad 간격 규칙(창 4)을 더했다. 풀, 클러스터, I-패널의 순서 규칙을 명시했다.
  - §2.3: selection split 저작 완료(18 클러스터, `check` 통과, manifest `0c0a64b1…`). I-패널 저작 완료(설계자 저작 한계). E2E 원천 누설 검토와 옵션 E/T+ 제시. admission 원천을 selection 14·15번으로 바꿨다.
  - 실행 패킷: run-spec 초안 16개의 workload를 채웠다. 남은 것은 U5s, U7r0·r1, U8c·n과 동결 시점 필드다.
  - 조율자 수용 결정: U3 쌍 동시 전송, 중단 95%·시작 90%, salt `gold_sha256`, 부분집합 봉인 쪽 선정.
  - 모델 호출 0회, 저장소 쓰기 0회, 봉인·비밀 폴더 열람 없음. 공개 test states에서는 ID와 quad 별칭만 추출했다.
- v2.2(2026-09-26, Run 담당, 조율자 전달 결정):
  - E2E 원천 옵션 E를 채택했다(§0-6, §2.3, §8). T+와 S는 기각 사유와 함께 남겼다. 봉인 위치, 공개 목록, salt·순위 재계산 검사를 정했다.
  - 쌍 동시 열의 정본 이름과 폐기 예정 별칭을 정리했다(§0-7, §1.4, §2.4, §2.6).
  - 통합 GAP 가운데 Run 몫을 §3.7에 넣었다: `score_tolerance` 동결과 명시 전달(§4.1), 반복 신뢰도 evidence는 U7r1에만, U2s 연결(코드 필요), freeze 셀 필드, private receipt 경로.
  - U2s 1차 지표를 `jev_choice_flip_rate`(min, 96)에서 `jev_choice_pair_consistency`(max, 24)로 바꿨다. 구현(`stability_summary`)은 rep1을 기준으로 rep2를 반복, order-rev·para를 변형으로 나눈다. v2.1의 "96 변형 호출 대비 flip"은 이 구조와 맞지 않았다. U2s는 동결 전이고 기술통계 단위라 가설 판정은 달라지지 않는다.
  - held-out 재빌드(통합 0015)를 반영하는 절차를 넣었다(§2.3). 생성기가 test gold 불변을 검사한다.
  - 외부 검증 X1·X2를 더했다(§0-8, §2.2, §3.4, §5-5, §11, 사용자 결정). 합계와 quota·Jev 문구를 고쳤다(§2.2, §7, §9).
  - 변경 이력을 §12로 옮겼다.
  - 모델 호출 0회, 저장소 쓰기 0회, 봉인·비밀 폴더 열람 없음.
- v2.2 보완(2026-09-26 23:5x, Run 담당, 조율자가 입력 도착을 알림):
  - quad 간격 규칙을 결정적으로 고쳤다(§8.1). 재빌드 manifest에서 v2.1의 뒤로 미루기가 U2s 마지막 자리에 위반 1건을 냈다. 이제는 막다른 곳에서 되돌아가 해시 순서의 다음 상태를 시도하므로, 결과는 규칙을 만족하는 사전식 첫 배열이다. 되돌아갈 일이 없는 U1·U2·U3의 순서는 그대로다.
  - 재빌드 공개본, `#para`, E2E 원천 목록, X1 수치를 반영했다(§2.2, §2.3, §7, §8, §9, §11). Replay 과제는 U7 `e2e-golfballs`, U8 `e2e-telescopes`로 확정되었다.
  - X1은 N=239이고 예산은 Astra 239/251, Jev 239다. Choice 단독 어댑터와 이진 채점이 없어 `blocked_by`로 막았다. X2는 변환 중이라 대기다.
  - 모델 호출 0회, 저장소 쓰기 0회, 봉인 폴더·X1 라벨 파일 열람 없음.
- v2.2 보완 2(2026-09-27 00시대, Run 담당, 조율자가 외부 데이터 준비 완료와 결정 5개를 전달):
  - §11을 외부 데이터 담당의 보완 초안과 병합했다. X1(239, 동률 21 제외, 클러스터 133)과 X2(240 풀, 웹사이트 클러스터 94, test_website 10이라 split별 구간은 최소 조건)의 데이터·지표·한계·공개 등급·예산을 채웠다.
  - 조율자 결정 9–13을 §0에 적었다: X2 listwise 유지, X1a 추가, X1 파생 파일 reproducible-cache, McNemar는 b·c만(p값 없음), Score-S 동시성은 0024 전까지 PENDING.
  - run-spec: X1a를 추가했다. X2의 workload를 채웠고, U0b·U4·U5s·X2의 harness를 Score-S 선택 dispatch로 정정했다(동시성·호출 시간 제한은 PENDING). U5p·U6a의 harness 표기도 고쳤다.
  - 통합 0019·0022(U2s 연결, run별 primary)를 반영했다(§1.3-14, §3.7-3). `PanelUnit`은 Choice와 Noul run을 함께 쓰므로 U0a와 U2s를 run 두 개씩으로 나눴다. 호출 수는 그대로다.
  - Choice 단독 `PanelUnit`(0025)이 없어서 U3도 막혀 있음을 적었다(§1.3-16, U3 초안 `blocked_by`).
  - 총량을 다시 계산했다: Astra 약 3,641, Jev 약 2,194(§2.2, §7), Jev 추정 약 $0.22(§9).
  - 모델 호출 0회, 저장소 쓰기 0회, 봉인 폴더·외부 정답 파일 열람 없음.
- v2.2 보완 3(2026-09-27, Run 담당, 조율자 전달: 0025가 PR head `020caa1dc`에 반영됨, 0024 교체본 대기):
  - run-spec 문구에서 부등호를 모두 없앴다("above/below", "at most/at least"). 계약의 자리표시 검사(`<[^>\n]+>`)에 U2c·U3 문구가 걸렸기 때문이다. 판정 기준 값은 그대로다.
  - U3에 0025 인자를 넣었다: `mode="paired-latency"`, `max_concurrency=2`, `pacing_s=1.0`, `timeout_seconds=180`. `blocked_by`를 지웠다. 분석 CLI와 `--record` 1회 규칙(§3.7-7), 시간 초과 대체 쌍의 제외 수 보고(§3.6)를 적었다.
  - X1a·X1: `latin`, `max_concurrency=4`, Choice 단독 칸 순서(짝수 A→B, 홀수 B→A)를 적었다. X1a 차단을 풀었다. X1 차단 패치 번호를 0026(채점)·0027(연결·CLI·서술 지표)로 고쳤다(§1.3-16, §11.10).
  - Score-S(U0b·U4·U5s·X2): `max_concurrency=4`, `timeouts={"llm": 180, "jev": 60}`을 채웠다. 전송 실패는 §4.2, 응답 계약 위반은 §3.1 오답이다. index에 "0024 교체본 확인 대기"로 표시했다.
  - U6a는 intent 패널 하네스가 고정 트리에 없어 `blocked_by`를 달았다(§1.3-8).
  - 총량은 바뀌지 않았다(Astra 약 3,641, Jev 약 2,194). 게이트 변화는 U3와 X1a의 차단 해제, U6a의 차단 표시다.
  - 모델 호출 0회, 저장소 쓰기 0회. 고정 트리는 `git archive`로 scratch에 풀어 검증에만 썼다.
- v2.2 보완 4(2026-09-27, Run 담당, 조율자 결정 두 가지):
  - 고정 SHA를 트랙별 두 개로 나눴다(§0, §1.1, §1.6). #1 `7cd052649`(0027까지)는 E 트랙, #2(0028–0030 포함)는 P·G·solo가 쓴다. #2 확정 때 `git diff --stat #1..#2`를 기록한다. 이에 맞춰 U0c를 Harbor 부분(U0c, #1)과 I-패널 batch(U0c-i, #2)로 나눴다. 호출 수는 그대로다.
  - 일시적 429 처리 규칙을 바꿨다(§4.1 분류표, §4.2, §4.3). 일시적 429는 `Retry-After` 대기 뒤 §4.2로 1회 대체한다. 한도·과금 429와 402는 `quota_exhausted`로 즉시 중단하고, 401·403은 `harness_error`로 중단한다.
  - X1 연결·서술 지표 패치 번호를 0030으로 고쳤다(§1.3-16, §11.10). 0026(채점)은 #1에 들어 있다. I-패널 하네스는 0029다(U0c-i, U6a).
  - 총량과 게이트 수치는 그대로다(Astra 약 3,641, Jev 약 2,194).
- v2.2 보완 5(2026-09-27 02:57:18 KST, Codex 인계 검토):
  - §1.6을 소스 불변 주장 대신 E 실행·분석의 #1 checkout 유지 통제로 정정했다. #2 후보의 `decision_handoff.py` 추출 리팩터와 10개 합성 시나리오 바이트 회귀(1 test 통과), 기준 소스의 #1 동일 해시, 이후 E 동작 변경·회귀 실패 시 동결 차단을 명시했다.
  - §4.1·§4.2에 비quota 429=`rate_limited`, 한도 code/type 목록, Retry-After 초·HTTP-date 0–120초, 기본 30초, `retry_wait_s`의 지연 제외를 반영했다. E #1의 중단 규칙은 유지했다.
  - U0c-i·U6a의 intent·paired-latency·동시성 2·Jev 엄격 합 허용치 1e-5·분석 CLI를 적었다. 0030/X1 및 0029/I-패널 코드 차단 해제와 남은 동결 조건을 구분했다.
  - X1의 X1a·selection-freeze(T·τ) 선행과 τ/T 없음에 따른 해당 보조 지표의 not-measurable을 명시했다. 외부 데이터 재적합은 금지한다.
  - U0b·U5p의 자연 과제 문구 파일과 SHA-256 `4202becf1707781de1379a1703595869762b34be2b50d65817900940c6e69f94`를 연결했다. 0024 대기 문구를 후보 소스 확인 상태로 정정했다.
  - 이 검토의 실험 모델·유료 호출 0회, Docker·infra·단위 동결·live 실행 0회. 봉인·비밀 폴더 열람 없음. 합성 회귀 검사는 scratch 소스에서만 실행했다. 문서 수정은 실행 재개 승인이 아니다.

- Codex 조율 확인(2026-09-27 03:00:26 KST): 고정 #2의 정확한 PR head CI 15개 success(배포 작업은 PR 범위 밖 skip), G-3 4군 965 tests 및 증명 27/27·29/29·19/19·10/10 통과. 소스 checkout 확보와 단위 동결은 구별하며, 동결·live 실행 보류는 유지한다. 상세 증거는 `codex-pre-freeze-20260927/`와 `handoff-snapshot-20260927/proofs/out/2f2b494d605c9306dcf1d94a2394e7576e959ace/`에 있다.

- 추가 실행 입력 검사(2026-09-27T03:09:19+09:00): 비공개 G 드라이버가 등록된 자연 과제 문구 SHA와 파일 bytes를 대조하고, X1 분석 진입점이 selection-freeze SHA를 확인한 뒤 고정 분석기를 호출한다. 안정 드라이버 통합 시험 27개 통과. 고정 #2 저장소 소스·모델·반복 수·규모는 변경하지 않았다.

- 2026-09-27 06:21:33 KST — §1.2.2: 새 계정 guard의 raw 퍼센트 해석·registry 초기화·이전 이력 보존, U1 사전 적합범위 해석 기록. U1 실제 호출 전이며 선택 입력은 변경하지 않음.


### 후속 E 실행 승인 기록 — 2026-09-26T21:45:04.666030+00:00

사용자는 “재생 검토 완료, U8c·U6b 진행 승인”으로 U0d·U0c 사람 검토와 후속 U8c·U6b 실행을 명시 승인했다. Source #3와 기존 연구 조건을 그대로 사용하며 새 계정 [account-withheld]/pro의 E/I-r2 lineage로 이어간다. 기존 r1 결과·동결은 보존하고 새 playback-check만 추가한다. U8n은 U0e의 유효 의미적 실패로 계속 차단한다. 호스트 guard만 검증된 새 계정판으로 교체하며 모델·규모·반복·동시성은 바꾸지 않는다.


### U0b 선택 전 호스트 원장 수리 — 2026-09-26T21:47:08.772822+00:00

G에서 생성한 자연 풀은 재생성하지 않는다. G/P 동일 연구 run ID에 대한 native 원장 중복 admission으로 P3 선택 실행이 호출 전에 거부되었다. P4 host wrapper에서 unit 식별자를 run_id:unit, call 식별자를 run_id:unit:raw로 결합해 native 원장에 전달한다. 기존 검증·예산·예약·정산은 native owner가 담당한다. 회귀13개 통과. Source #2, 연구 spec bytes, 후보 풀, 선택기·허용치·입력·분석은 보존한다. 새 P freeze는 원 G 결과 resolved 경로와 새 host wrapper SHA를 바인딩한다.


### P5 Score/G 후속 실행 전 연결 — 2026-09-26T22:24:14.428122+00:00

U0b 통과와 허용치0.03 동결을 근거로 U1과 독립인 U5p를 진행한다. 자연12과제는 기존 native best_of4/data_analyst/no-tools child AgenticLoop 및 후보 judge가 Astra xhigh 구독으로 한 번 생성한다. 기존 reset_strategy의 직접 판정/no-root 문구를 이 사실로 정정한다. 모델·문구·규모·폭·재생성 금지는 그대로다. 새 Score host guard는 기존 CallControl로 각 호출의 STOP·계정·lock·cap을 확인하고 --quota-live의300회 검사와 시작 후 unknown 정산을 보존한다. native순서·동시성4·180/60초·대체1회/2% 규칙은 유지한다. 자체52시험과 독립 예외/경계 검증 통과. 새 분석기는 기존 native 통계·채점을 재사용하고 실제 종료영수증과 전체행렬을 검증한다. bootstrap seed와 entry SHA는 각 prospective spec에 바인딩한다. U5s의 분모는 실제 U5p complete 목록으로만 확정한다. U4/X2 봉인 gold 채점·공개는 아직 승인되지 않았다. 이전freeze와 소스 #2 bytes는 보존한다. 자료: codex-pre-freeze-20260927/remaining-u-preparation-20260927/score-main-r5/.


### U1 전체 단위의 한정 재시행 — 2026-09-26T22:26:09.768012+00:00

사용자의 “차단된 시행도 다시 재시행해”와 계정 교체 후 재개 지시에 따라, P4 U1의86/640 불완전 실행은 invalidated로 보존하고 P5에서 원640호출 전체를 한 번 새로 수행한다. 이 사전 기록은 실패 cell을 §4.2 전송대체로 소급분류하지 않는다. 새 실행은 같은 source #2·Astra xhigh·Jev1.13.0·160selection상태·입력순서·호출시간·동시성·예산·반복수·144headline/16서술 범위를 유지한다. P4의85유효응답과1APIError를 새 실행에 섞거나 T/τ에 적합하지 않는다. P5 전체행렬과 정상종료를 만족할 때만 기존 고정 분석기로 T/τ를 한 번 적합한다. 중단 사유가 다시 발생하면 기존 규칙으로 종료하고 이 회복 범위에서 추가로 반복하지 않는다. APIError의 원인은 여전히unknown이며 수리되었다고 주장하지 않는다. 새 host wrapper는 해당호출의 예외에서 제한된 code/type/status/request_id만 기록한다(알수없는값null,본문·header·token저장없음); 분류·대체·측정지연에는 쓰지 않는다. 26합성시험통과, 이전freeze/source불변. U5p 실제 실행 종료 뒤 전역lock 아래 순차실행한다.
