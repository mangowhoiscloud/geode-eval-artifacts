> Historical method/decision record; current findings and corrections are in the package index. Personal paths and account identifiers have been withheld.

# 06 · 한 번의 성공과 반복의 신뢰도

2026-09-26 · 1차 자료에 근거한 설계 보강. **실행 전 초안이며 새 실험 결과가 아니다.** 모델·effort·실행 횟수·예산·기존 1차 지표는 바꾸지 않는다. 실행 재개에는 05 §0의 게이트와 사용자 지시가 필요하다.

## 1. 출처 계보와 확인 범위

| 원문 | 직접 확인한 주장 | 이번 설계에서의 역할 |
|---|---|---|
| [Anthropic, Demystifying evals for AI agents (2026)](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) | trial은 과제의 한 시행. pass@k는 k회 중 적어도 한 번 성공, pass^k는 k회 모두 성공. 작업의 실제 결과와 transcript의 성공 주장을 구분 | 제품 목적에 따라 성공 기회와 일관성을 나눠 보고 |
| [Kulal et al., SPoC (NeurIPS 2019), §2·6](https://proceedings.neurips.cc/paper/2019/file/7298332f04ac004a0ca44cc69ecf6f6b-Paper.pdf) | Anthropic의 pass@k 링크가 가리키는 원문. 논문 자체의 명칭은 **success rate at B**: 컴파일·실행 예산 B 안에서 테스트를 통과한 프로그램을 찾은 과제 비율 | 피드백을 쓰는 탐색의 예산별 성공. 이를 IID 표본의 pass@k 추정식과 동일시하지 않음 |
| [Chen et al., Evaluating Large Language Models Trained on Code (2021), §2.1·식 1·부록 A](https://arxiv.org/pdf/2107.03374) | 문제별 N개 표본에서 성공 c개를 세어, n개 중 하나라도 성공할 조합 비율을 계산. 성공률을 식에 바로 대입하는 plug-in 추정의 편향도 설명 | pass@n 조합 추정식과 과제별 평균 |
| [Yao et al., τ-bench (2024), §3](https://arxiv.org/pdf/2406.12045) | 같은 과제를 독립적으로 반복했을 때 n회 모두 성공할 비율을 pass^n으로 측정. 단일 시행 reward만으로 정책 준수 전부를 보장하지는 않음 | pass^n 조합 추정식, 초기 상태 재설정, strict success 필요성 |

원 논문은 k를 쓰고, 영상은 사용자가 요청한 **n**으로 표기한다. 기호만 바뀌며 정의는 같다.

### 코드까지 확인한 1차 구현

- [OpenAI human-eval/evaluation.py, commit 6d43fb980f9fee3c892a914eda09951f772ad10d](https://github.com/openai/human-eval/blob/6d43fb980f9fee3c892a914eda09951f772ad10d/human_eval/evaluation.py#L13): `estimate_pass_at_k`. 표본 수가 k보다 적으면 그 k의 집계를 내지 않는다.
- [Sierra τ-bench/run.py, commit 59a200c6d575d595120f1cb70fea53cef0632f6b](https://github.com/sierra-research/tau-bench/blob/59a200c6d575d595120f1cb70fea53cef0632f6b/tau_bench/run.py#L167): `display_metrics`가 과제별 성공 횟수의 조합 비율을 평균한다. 시행마다 새 환경을 만드는 경로도 확인했다.
- τ-bench 코드의 예외를 reward 0으로 바꾸는 처리는 이식하지 않는다. GEODE는 인프라 오류를 `invalid / unknown`으로 보존한다. 전역 trial 개수만 믿지 않고 **각 과제의 계획 행렬 완전성**을 검사한다.

## 2. 세 종류의 반복을 먼저 분리

| 축 | 뜻 | GEODE 예 | 성공 지표의 단위 |
|---|---|---|---|
| 후보 폭 w | 한 선택 단계에 제출한 후보 개수 | Score 풀의 후보 4개 | 후보별 독립 oracle → 풀의 coverage → 선택한 후보의 성공 |
| 수정 깊이 d | 같은 실행 안에서 피드백을 받고 고친 횟수 | Reflection → hold → root 수정 → 재판정 | 전체 과제 시행 1회에 포함. 수정 횟수·비용은 별도 |
| 반복 수 N | 초기 상태를 재설정한 전체 시행 수 | 자연 E2E 과제당 각 arm 2회 | 각 시행의 strict success를 입력으로 pass@n·pass^n |

판정 호출 6개, 결함 3종, 후보 4개를 독립 E2E 6·3·4회로 바꾸어 세지 않는다. 서로 다른 정책·결함·질문 변형도 같은 반복 집합으로 합치지 않는다.

## 3. 정의와 추정

과제 i마다 같은 동결 정책으로 N_i번 실행하고 strict success가 c_i번이면, n ≤ N_i에서:

```
pass@n = mean_i [1 − C(N_i − c_i, n) / C(N_i, n)]
pass^n = mean_i [    C(c_i, n)       / C(N_i, n)]
```

- C(a,b)는 조합이며 a < b이면 0이다. 과제별로 계산한 뒤 같은 가중치로 평균한다.
- n=1에서는 두 값이 같다. 완전한 동일 크기 행렬에서는 기존 시행 성공률과도 같다.
- 특정 과제의 참 성공확률 p, IID 시행이라는 이론적 조건에서는 각각 1−(1−p)^n과 p^n이다. **모든 과제를 합친 관측 성공률을 이 식에 대입하지 않는다.** 과제별 난이도 차이를 지우고 plug-in 편향도 만든다.
- 모델·프롬프트·도구·verifier·예산·초기 상태·수정 정책이 같아야 한다. 반복 사이에 이전 답이나 Reflection 메모리가 유입되지 않도록 세션·파일·캐시의 reset 경계를 동결한다.
- 외부 provider drift 등으로 IID를 확증할 수 없는 작은 운영 실험은 “동결 조건의 두 시행에서 관측된 일관성”으로 한정한다. 모든 미래 요청의 신뢰도로 일반화하지 않는다.

### 정의 예시 (GEODE 실측 아님)

| 과제 | 첫 시행 | 두 번째 시행 | 둘 중 하나 성공 | 두 번 모두 성공 |
|---|---|---|---|---|
| A | 성공 | 성공 | 1 | 1 |
| B | 성공 | 실패 | 1 | 0 |
| C | 실패 | 실패 | 0 | 0 |

pass@1 = pass^1 = 3/6, pass@2 = 2/3, pass^2 = 1/3. 이 표는 용어 설명용이며 실험 결과·기대 성능·달성 기준에 넣지 않는다.

## 4. 어떤 용도에 어떤 지표를 쓸까

- **여러 답 중 쓸 수 있는 답을 확보하는 탐색:** pass@n. 단, oracle이 성공 후보를 알아본다는 상한이므로 실제 선택기의 성능과 분리한다. 후보를 모으는 비용과 선택 비용도 포함한다.
- **매 요청마다 안정적으로 같은 계약을 지켜야 하는 자동화:** pass^n. 의도 라우팅, 권한 확인, 완료 승인에서는 성공을 한 번 더 얻는 것보다 실패가 반복되지 않는지가 중요하다. n과 실제 반복 수를 함께 표기한다.
- **실제로 배포한 고정 예산의 정책:** 한 번의 전체 시행 성공률, 실패·거짓 완료·복구·전체 시간/비용이 기본이다. pass@n 또는 pass^n만으로 배포 승인하지 않는다. n회 독립 실행을 실제로 운영하지 않았다면 그 예산으로 동작하는 시스템처럼 소개하지 않는다.
- **오류를 고친 시행:** 첫 후보 실패와 최종 복구 성공을 함께 남긴다. pass^n의 n은 수정 횟수가 아니라 처음부터 다시 시작한 시행 수다.

## 5. 현재 예정된 단위에 적용

| 단위 | 고정된 계획 | 추가로 보고할 것 | 보고하지 않을 것 |
|---|---|---|---|
| 자연 E2E U7r0+r1 | 12과제 × 2회 × A/B = 48 rollout. C는 기존 조건부 승인 유지 | 동일 계약의 r0/r1을 합쳐 arm별 pass@1·pass@2·pass^2. A/B 차이는 같은 과제 집합에서 계산. 시행별 복구·거짓 완료·전체 비용 병기 | 2회를 넘는 pass^n, 운영 신뢰도 확정, 1차 지표 교체 |
| Intent Harbor U6b | 3과제 × A/B × 1회 = 6 rollout | pass@1에 해당하는 strict success와 의도·대상·추가 조회 오류 | pass^2. 중요한 용도여도 반복이 없으면 산출 불가 |
| 주입 U8c/U8n | 과제·결함 조건별 각 arm 1회 | 조건별 복구율, 첫 오판, 수정 깊이·사용량·시간 | 서로 다른 결함 조건을 묶은 pass^3 |
| Score U4/U5 | 후보 4개를 고정해 선택기를 비교 | pool-random@1, oracle-coverage@4, selected success, oracle-best 선택률, 생성/선택 비용 | 통제해 구성한 후보를 IID 생성 4회로 취급한 pass@4 |
| 안정성 U2s | 동일 질문 rep1/rep2 + 순서 역전 + 바꿔쓴 질문 | 동일 질문 두 번의 pair consistency·정답 일관성. 순서·표현에 대한 flip rate는 별도 | 4변형을 4회 IID 반복으로 묶은 pass^4 |
| 패널 U2, 의도 U6a | 항목당 각 계약 1회 | 정확도·확률 보정·오류 탐지·의도와 대상의 joint 정확도 | 개별 항목 pass^2 또는 여러 조건을 반복으로 합산 |

**Score 수용 기준:** `acceptable`은 독립 과제 oracle의 성공 조건으로 동결한다. 부분 정답 등급이나 “풀에서 가장 나음”만으로 수용 성공을 만들지 않는다. 모든 후보가 실패해도 oracle-best 선택은 맞을 수 있으므로 두 지표를 병기한다.

```
pool-random@1      = mean_pool [acceptable candidates / pool width]
oracle-coverage@4  = mean_pool [at least one acceptable candidate]
selected success  = mean_pool [selected candidate is acceptable]
gap closed        = (selected − pool-random@1) /
                    (oracle-coverage@4 − pool-random@1)
```

분모가 0이면 gap closed는 not-measurable이다. 음수도 숨기지 않는다. 실패한 selector의 fallback은 독립 과제가 통과해도 selector 성공으로 세지 않는다. 생성 과정의 독립성·샘플링 정책을 따로 동결한 미래 실험만 생성 pass@4를 보고할 수 있다.

## 6. 기존 데이터 스캐폴드에 붙이는 경로

`run-spec + native result + verifier receipt`
→ 기존 `e2e_trials`의 `case_id / repetition / arm / strict_success`
→ 계약 해시·초기 상태·정책·예산이 같은 반복만 묶음
→ 기존 `primitive_summary`와 `analysis.json`의 **보조 지표**
→ 결과 표·KO/EN 영상.

새 원본 저장소나 별도 성공 판정기는 만들지 않는다. 집계는 기존 strict success를 읽는다. source revision, policy/reset digest, 입력·verifier hash가 다르면 r0/r1을 합치지 않는다.

보조 지표에 `n`, `planned_tasks`, `complete_tasks`, `incomplete_tasks`, `expected_repetitions`, `observed_repetitions`, `valid_repetitions`, `run_spec_sha256s`, 원천 행 포인터를 남긴다. 집계에 들어갈 모든 과제·시행을 **실행 전에** 고정한다.

- 의미적 실패와 판정 출력 무효(valid/failed)는 실패로 분모에 포함한다.
- 인프라 무효·미실행·증거 누락은 unknown이다. 0이나 성공으로 채우지 않는다. 계획 행렬이 불완전하면 해당 예정 집계는 not-measurable이다. valid-only 기술통계가 필요하면 별도 이름과 실제 분모로만 낸다.
- 승인된 replacement는 원 시행을 대체하는 lineage이며 반복 수를 늘리지 않는다. 원본은 보존한다.
- 각 반복의 전체 비용을 합쳐 n회 예산을 밝힌다. 성공한 시행만 골라 시간·비용을 보고하지 않는다.

## 7. 동결 전에 할 무모델 검사

1. n=1의 두 지표 일치; 성공 수 0·N의 경계값.
2. 완전한 행렬에서 pass@n은 n에 대해 비감소, pass^n은 비증가.
3. 위 세 과제 예시가 1/2·2/3·1/3인지 확인.
4. N<n, 반복 중복, 불완전한 과제 행렬, 계약 불일치, unknown을 집계 거부.
5. 후보 순서 변형·repair round·replacement를 새 독립 반복으로 세지 않는 회귀 검사.

이 문서의 수식 검산과 영상용 예시는 새 GEODE 모델 호출이나 verifier-backed 결과를 뜻하지 않는다. Build/Run 담당은 기존 지표 모듈에 이 계약과 검사들을 반영한 뒤 G-3를 다시 증명한다.
