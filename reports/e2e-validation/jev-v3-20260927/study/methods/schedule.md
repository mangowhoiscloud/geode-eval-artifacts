> Historical method/decision record; current findings and corrections are in the package index. Personal paths and account identifiers have been withheld.

# 현재 승인 보완 — 2026-09-27 06:53:05 KST

U0d/U0c 사람재생검토와 U8c/U6b source#3·새계정 E/I-r2 실행은 명시 승인되었다. 아래 #3 admission까지만 승인이라는 문구는 당시 이력이며 후속 승인 범위는 RESUME-KIT의 최신 체크포인트와 playback-approval-20260927.json을 따른다. U8n·arm C·gold개봉·병합·공개를 이 승인에 포함하지 않는다. 순서·규모·동시성 규칙은 아래 그대로다.

# 실행 스케줄: 두 트랙, 비중첩, 쌍 동시 슬롯

권위는 [05 v2.2](05-preregistration.md) §1.6–§1.7, §2.4–§2.6, §7, §11.9다. 원래 E 트랙 고정 #1은 무효 실행 이력과 함께 보존한다. **현재 승인된 E admission U0d→U0e→U0c는 고정 #3 `7f32ff272d1b07a6404c593e74dad727857e0bd8`와 `-r1` 새 lineage, `freeze/pins.e-recovery.json`을 쓴다.** P·G·solo는 고정 #2를 유지한다. #3 재실행 승인은 본실험 승인을 포함하지 않는다. 이 문서는 실행 순서를 운영용으로 풀어 쓴 것이다. 단위를 줄이거나 quota 때문에 미루지 않는다.

## 1. 트랙과 전역 실행 잠금

| 트랙 | 내용 | 동시성 | 단위 |
|---|---|---|---|
| E | Harbor E2E 쌍 동시 슬롯 | 슬롯 안 arm 2개(C 포함 3개), 슬롯 사이는 순차 | U0c(Harbor 셀), U0d, U0e, U0f, U6b, U7r0, U7r1, U8c, U8n |
| P | 판정 패널(직접 호출)과 Score-S 선택 | 동시 호출 ≤4(I-패널은 2) | U0a-c/n, U0b(선택 호출), U0c-i(I-패널 batch), U1c, U1n, U2c, U2n, U2s-c/n, U4, U5s, U6a, X1a, X1, X2(v2.2) |
| G | 후보 생성(`delegate_task(best_of=4)` 에이전트 실행) | 1 | U0b(자연 풀 1개), U5p |
| solo | 지연 패널 | 동시 쌍 1개 | U3 |

규칙:
- 호스트에 잠금 파일을 하나 둔다. 위치는 `<run-root>/.execution-lock`이고, 기록 필드는 모드(`e2e-slot`, `panel-unit`, `gen`, `latency-solo`), 소유 `run_id`, 시작 시각이다. 한 번에 한 모드만 잡을 수 있다.
- **E 단위는 시작하면 그 단위의 모든 슬롯이 끝날 때까지 P·G·solo를 시작하지 않는다.** P·G 단위도 시작하면 끝까지 간다. 단위는 서로 겹치지 않는다.
- 준비된 단위가 여러 개면 E가 먼저다. 사용자 결정에 따라 패널은 E2E가 없는 빈 시간에 돈다. E가 게이트(재생 검토, arm C 결정)에 막혀 있을 때 P·G를 돌린다.
- U3(solo) 동안에는 우리 쪽 무거운 작업을 멈춘다. 데이터 정제 배치, 다른 Codex 사용, Docker 빌드가 여기에 해당한다. 같은 계정의 영상 세션은 통제할 수 없으므로 `unknown`으로 기록한다.
- 잠금 위반(겹침)이 생기면 나중에 시작한 단위를 중단하고, `failure_class=schedule_overlap`인 인프라 무효로 처리한다.

## 2. 의존 게이트

```
G-1..G-5 ─┬─ U0a (P) ───────────────┐
          ├─ U0d, U0e, U0c (E, 쌍) ─┼─ 사용자 재생 검토 ─┬─ [E2E 원천 준비] ─ U8c → U8n (E)
          └─ U0b (G+P) ─────────────┘                   ├─ U6b (E)
                                                        └─ (U7 게이트의 일부)
U0a 통과(selection split은 v2.1에서 저작 완료) → U1c/U1n (P) → selection-freeze.json
    → U2c/U2n (P) → U2s (P) → U3 (solo) → test gold unseal → U2c 분석 → arm C 결정(05 §6)
arm C 결정 + [E2E 원천 준비] → [승인: U0f (E, C 단독) →] U7r0 (E) → U7r1 (E)
[E2E 원천 준비] = 옵션 E 공개 목록 e2e-sources.json 도착 → 조율자 통지 → make_packet --e2e-sources 재생성
                  (봉인 원천 20개는 e2e-sealed-DO-NOT-OPEN/, Run은 열지 않음. 원천이 패널 gold와 무관하므로 U8은 unseal을 기다리지 않음)
U0b → score-tolerance-freeze.json → U4 (P);  U0b → U5p (G) → U5s (P);  I-패널 + U0c-i → U6a (P)
0025 → X1a (P) → [X1a 통과] + U2c/U2n 완료 → X1 (P)
U2c/U2n 완료 + score-tolerance-freeze.json + 0024 → X2 (P)
외부 데이터는 도착했다(X1 manifest 03002e70…, X2 manifest 413fdbcc…, 05 §11.2)
```

`run-specs/index.json`은 27개 단위의 초안 목록이며 `depends_on`만으로 전체 게이트를 표현하지 않는다. 아래 설명은 실행 패킷을 바꾸지 않고 기존 조건을 풀어 쓴 것이다.

- legacy `U0a`는 U0a-c·U0a-n으로 분리된 초기 점검을 뜻한다. U1c/U1n 전에 해당 Choice·Noul admission 통과를 확인한다.
- U0f는 arm C admission 착수 조건과 별개로 같은 소스 U0d 통과·사용자 재생 검토가 필요하다. C를 넣는 U7에는 U0f 통과·재생 검토도 필요하다. 05 §6의 U0f 통과 조건은 U7에 C를 넣기 전 조건이다.
- U4·U5s·X2는 U0b 뒤의 `score-tolerance-freeze.json`을 사용한다(05 §3.7). U5s의 유효 풀·분모는 U5p 뒤 확정한다.
- X1·X2 본실행은 U2c/n 완료뿐 아니라 U2s→U3→unseal→arm C 결정의 핵심 운영 순서 뒤에 배치한다(§3, 05 §11.9). X1a 초기 점검은 기존대로 P 빈 시간에 먼저 할 수 있다.
- `blocked_by=[]`는 코드 차단 항목이 없다는 뜻이며, 위 선행 게이트나 사용자 동결·실행 승인을 대신하지 않는다.

조율자가 준 설계 순서는 "U0 → M7 selection → τ 동결 → M7 test·안정성·지연 → Score → intent → M8-N → M8-I"다. 병렬 스케줄에서도 이 선행 의존은 모두 지킨다. 다만 E 트랙은 게이트만 통과하면 M7과 독립적으로 진행할 수 있다. 예를 들어 U8은 τ와 무관하므로 재생 검토 직후 시작할 수 있다.

## 3. 기본 진행표(이벤트 구동)

| 순서 | 트랙 | 단위 | 시작 조건 | 끝나면 |
|---|---|---|---|---|
| 1 | E | U0d(2슬롯) → U0e(1슬롯) → U0c(Harbor 1슬롯) | G-1..G-5, **현재 승인된 #3/r1 `7f32ff272d1b`**(05 §1.7); #1 원본 보존 | cast 준비. 사용자 재생 검토를 바로 요청하고, 검토하는 동안 2–7을 진행한다 |
| 2 | P | U0a-c·U0a-n | 1 뒤, selection admission 8 상태, 고정 #2 | 무효율·허용 분류 기록 |
| 3 | P | U0c-i(I-패널 admission batch) | 2 뒤, 고정 #2(0029) | — |
| 4 | G+P | U0b(`score_tolerance=0.05`로 실행) | 3 뒤 | `score-tolerance-freeze.json` 동결(05 §3.7-1), quota 보정 r 계산 |
| 5 | P | U1c → U1n | selection split, U0a 통과 | `selection-freeze.json` 동결 |
| 6 | P | U2c → U2n → U2s | 5 | — |
| 7 | solo | U3 | 6 | test gold unseal → U2c 분석 → arm C 결정 |
| 8 | E | U8c → U8n | 재생 검토 승인 + E2E 원천 준비(옵션 E 목록, unseal과 무관) | (5–7 중 승인이 오면 진행 중인 P 단위가 끝난 뒤 시작) |
| 9 | E | [U0f →] U7r0 → U7r1 | arm C 결정 + E2E 원천 준비 | 반복 신뢰도 집계 가능 |
| 10 | E | U6b | U0c 재생 승인 | — |
| 11 | P | U4 | U0b | — |
| 12 | P | U6a | I-패널 도착, U0c-i 8/8 수용 | — |
| 13 | G → P | U5p → U5s | U0b | — |
| 13a | P | X1a(가장 긴 두 상태 × 2 엔진) | G-1..G-5 + 0025(Choice 단독 `PanelUnit`) | 통과해야 X1 동결. P 빈 시간 아무 때나 |
| 14 | P | X1(239 상태) | X1a 통과 + U2c·U2n 완료 + selection-freeze(T·τ·해시), #2의 0025·0026·0030 | 외부 타당도(Choice) 기록. U2s·U3보다 앞서지 않는다 |
| 15 | P | X2(240 풀, listwise 포함) | U2c·U2n 완료 + `score-tolerance-freeze.json` + 0024 | 외부 타당도(Score). 300호출마다 quota 확인. 순차면 약 2–12시간이라 E 트랙이 오래 막힌 빈 시간에 둔다 |

- 모든 단위 시작 전에 §7 quota 투영(90% 규칙)을 적용한다. 멈추면 초기화를 요청하고, 새 G0를 기록한 뒤 같은 단위를 시작한다. 순서는 바뀌지 않는다.
- 재생 검토 승인이 늦어지면 8–10이 뒤로 밀리고 P 단위가 먼저 돈다. 이 경우에도 단위 구성은 그대로다.
- X1·X2(v2.2, 사용자 결정)는 P 트랙 빈 시간에 돈다. U2c·U2n 뒤에만 시작할 수 있고, U2s → U3 → unseal → arm C 결정의 임계 경로보다 앞서지 않는다. 그래서 실제로는 7 뒤에, E 트랙이 게이트(재생 검토, E2E 원천, arm C 결정)에 막힌 시간에 11–13과 함께 돈다.

## 4. 참고용 우선순위(결과 가치 순)

이 목록은 판단 참고용이다. 축소, 연기, 순서 변경의 근거로 쓰지 않는다.

1. U2c/U2n: 핵심 질문인 판정 신뢰도(정확도·보정·오류 탐지)
2. U7r0: 자연 E2E와 Replay
3. U8n/U8c: 주입 복구, Noul의 두 조건, Replay
4. U7r1: 같은 조건 두 시행의 일관성(pass@2, pass^2)
5. U3: 쌍 동시 지연
5a. X1·X2: 외부 타당도(v2.2, 사용자 결정). 결론을 대체하지 않는 별도 층
6. U6b/U6a: intent
7. U4: Score 통제 풀
8. U2s: 안정성
9. U5p/U5s: Score 자연 풀
