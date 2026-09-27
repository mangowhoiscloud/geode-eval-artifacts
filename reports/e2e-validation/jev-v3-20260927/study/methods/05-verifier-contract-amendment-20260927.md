> Historical method/decision record; current findings and corrections are in the package index. Personal paths and account identifiers have been withheld.

# I6 과제 계약 전달 및 실행 예산 표기 정정 — 전향 변경기록

적용 시각 2026-09-27T19:53:04+0900. 사용자가 남은 기술 과제 해결·실험 종료·main 병합·영상 완성을 위임한 범위에서 조율자가 적용한다. 아직 새 I6/E6 동결·모델 호출은 없다. 이전 사전등록과 원 실험 파일은 수정하지 않는다.

## 변경 범위

I6는 source7 `1236ce96c8c5a79699d98f5c960b7a699c1f228a`를 사용한다. 기본 판정기에 명시적 task system override를 기존 비밀 패턴 가림·4,000자 제한·JSON 문자열 경계로 전달하고, 같은 요청의 prior/current 관측과 이전 요청의 retained_context를 구분한다. 전체 system/memory/suffix나 oracle 정답을 공급하지 않으며 judge 자체 규칙은 유지한다. 판정기에 주어지는 정보가 달라지므로 source6와 행동 동등을 주장하지 않는다.

모델 Astra xhigh 구독/Jev1.13.0, 입력·도구·순서·외부 verifier·엄격 성공 기준, root540초/agent570초/watchdog1290초/cleanup120초, 6라운드와 검증 후 보정2회, 병렬 arm2개는 유지한다. 새 I6 admission2셀→독립 원자료 감사·실제 위임 재생→같은 소스 playback 기록→natural 전체6셀을 한 번 측정한다. 실패나 무효는 보존하고 성공할 때까지 반복하지 않는다. U7은 source5와 원 과학 계약을 유지하는 새 계정 운영 계보 E6에서 12과제×3arm×2반복=72셀을 측정한다.

## 계획 호출수와 실제 상한을 구별한다

기존 05 §2.2는 budget.limit를 E2E 롤아웃당 Astra10회 상한으로 적었고 §4.3은 초과 시 중단·not-measurable을 요구했다. 현재 I/E 실행기는 이 숫자를 quota 시작 투영에 사용하는 계획값으로 읽으며, 그 횟수에서 모든 Astra 호출을 막는 단위 호출 계수기는 구현돼 있지 않다. **이 문서·구현 차이를 기존 결과에 소급해 적합하다고 처리하지 않는다.** I5 natural은 native valid6/6·strict0/6·mixed를 원 파일에 보존하며 계획60 대비 실제75 Astra(+25%)인 프로토콜 이탈을 별도 표기한다. 사후 확증 결과로 사용하지 않는다.

이 변경기록 이후의 I6 및 새 계정 E6에 한해서 05 §2.2/§4.3의 Astra 호출수 상한 문구는 운영 점예측으로 대체한다. 기존 필드 budget.limit 및 planned_astra_call_cap라는 이름은 호환상 유지하지만 여기서는 hardcap으로 해석하지 않는다. 실제 제약은 위 시간·라운드·보정 횟수, Jev 비용 원장, 계정/quota 가드이며 새 runtime 횟수 제한은 추가하지 않는다.

- I6 admission 계획 Astra13회: 동일 입력 직전 완결 I5의 A7+B6을 근거로 한다.
- I6 natural 계획 Astra75회: 동일 전체 입력 직전 완결 I5의 A39+B36을 근거로 하며 기존60의 과소예측을 정정한다.
- E6 U7 각 반복 계획 Astra360회는 기존 source5 frozen 계획을 유지한다.

13/75는 하나의 source6 관측에 근거한 점예측이다. source7의 기대값·통계적 상한을 입증하지 않으며, 수정 후 호출수가 줄어든다고 가정하지 않는다. 별도 `verification-contract-followup-20260927/call-envelope.md`의 288/864는 정상 context·라운드당 helper1회 아래 여러 보수 경로를 합친 민감도 계산으로만 제시한다. 제한 없는 helper 다중호출, context 복구/compaction, 서버 내부 작업은 그 계산에도 포함되지 않아 hardcap이 아니다. 이 큰 조건부 수치를 실제 예상 호출수와 동일시하지 않는다.

## 새 계정과 실행 전 증거

실제 새 계정의 안전한 지문/plan/G0와 단일 usage window/reset를 확인한 뒤 guard에 결속한다. 이전 계정·원장 행을 고쳐 쓰거나 이전 r를 임의로 가져오지 않는다. source7 필수 admission의 실제 종료 호출과 사용량으로 native r를 보정하고, 같은 계정·window의 I6 natural 및 E6 U7 시작 판단에 적용한다. native calibration은 지문/plan만 필터하므로 reset/window 경계는 별도 sidecar로 확인하며, 불일치하면 후속 실행을 시작하지 않는다.

시작 직전 native `used_now + r × planned/100`의 반올림 전 값이90% 이하여야 한다. r가 없는 첫 admission은 기존 calibrating 동작으로 현재 사용률을 판단하며, 저사용 새 계정이라는 관측이 필요하다. r 계산식이나90/95% 수치는 바꾸지 않는다. 현재 슬롯 quota 가드는 계획이300을 넘을 때 중간 슬롯에서1회 조회한다. 따라서 I6의13/75에는 중간 quota 조회가 없고 E6 U7의360에는1회다. 이는 연속 감시나300호출마다 실시간 차단을 보장하지 않는다. account/STOP/preflight만 매 슬롯 점검한다. 조회한 사용률95% 이상 또는 한도 오류는 기존 중단 규칙을 적용한다. 이 cadence를 새 I6/E6의 전향 운영 계약으로 명시한다.

source7 정확한 head CI 필수10/10, 관련회귀1989개, 독립설계16개와 별도코드검토가 완료됐다. G3는1038테스트/85증명 통과이며 clean checkout은 `[local-path-withheld] 최초 로컬 locale 오류의 실패기록은 보존하고, 설치된 en_US.UTF-8로만 정정한 검증을 채택한다. 새 source archive·runner/guard/protocol·입력/동결·인프라 proof·새 계정 정보는 실제 준비 후 각각 해시로 결속한다. 아직 새 실행 준비 완료나 실측 성공을 주장하지 않는다.

위임 검토는 `review_authority=delegated_agent`, `human_reviewed=false/deferred`로 남긴다. 리플레이는 재구성 화면이며 점수나 지연의 권위가 아니다. 원 native 분석·failure lineage·부분 시행·unknown 및 실제청구 미확인은 보존한다.
