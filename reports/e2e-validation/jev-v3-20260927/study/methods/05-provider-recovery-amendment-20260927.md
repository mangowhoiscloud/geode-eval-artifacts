> Historical method/decision record; current findings and corrections are in the package index. Personal paths and account identifiers have been withheld.

# U7 제공자 호출 장애 뒤 한 번의 별도 운영 복구 계보 — 실행 전 변경기록

작성 시각: 2026-09-27T13:42:56.942075+00:00. 상태: 조율자 검토용 prospective 기록. 이 파일은 성공·제공자 회복·새 동결·새 실호출이 발생했다는 기록이 아니다. 사용자에게서 이미 받은 중단 시행 재시행·기술 과제 해결·모든 태스크 종결 요청과 완료 위임에 따른 최소 후속 준비이며, 실제 시작은 조율자가 아래 기존 가드를 확인한 뒤 수행한다. 완료 위임 원문은 `codex-pre-freeze-20260927/remaining-u-preparation-20260927/budget-recovery-20260927/completion-delegation-20260927.json`에 보존돼 있다.

## 이미 관측한 실패와 범위

E6 source5 U7r0은 36셀 중 21셀을 수집했다. 유효 strict 성공 19셀과 인프라 무효 2셀을 보존하고 첫 invalid에서 중단했으며, 15셀은 미시작이다. 주지표는 not-measurable, native hypothesis_status는 invalidated다. B는 ReadTimeout 뒤 HTTPStatusError, C는 ReadTimeout 두 번이다. 공개 exports에는 HTTP 상태/요청 ID가 남지 않아 제공자 원인이나 회복 여부를 확정할 수 없다. B/C root runtime은 약107.28/105.70초로540초를 소진하지 않았다. 기본 Jev HTTP client timeout30초는 유지한다. E6 U7r1은 native 선행 조건 `U7r0.complete=true`를 충족하지 못해 차단된 상태로 남긴다.

이 기록은 05 §2.4·§4.2의 E2E 첫 invalid 중단·셀 대체 금지·원본 무효 보존을 바꾸지 않는다. 기존 E6를 수정하거나 불완전한 r0 뒤 r1을 강제로 시작하지 않는다. **추가 실행 범위만 새 E7 계보의 U0f 2셀 한 번, 이후 조건부 U7r0 36셀과 U7r1 36셀 각각 한 번으로 한정**한다. 따라서 최대74개 새 셀이다. 이는 서비스 상태를 확인한 뒤 별도 전체 계보를 관측하는 전향적 운영 복구이며, 원래 등록된 전체 노출 횟수가 증가한다는 사실도 공개한다.

## 고정 조건과 별도 계보

- E7 경로: `[local-path-withheld] source5 `1f6553431932040336cadcddb26893e30ebbb706`, pin `[local-path-withheld] source6/7의 숫자·capture·의도 judge 수정은 섞지 않는다.
- E6와 동일한 runner/dispatcher/guard 실행 코드와 source archive, task/payload/prompt/도구/과제 순서/반복별 ABC 시작 순서/τ0.50/분모를 그대로 사용한다. selection 재적합·원 답변 재채점은 없다.
- root/repair/reflection 및 Astra 판정은 GPT-6 Astra xhigh 구독, Jev는1.13.0. root540·Harbor570·setup600·verifier30·watchdog1290·cleanup120초, root 턴6라운드와 최대2회 verification continuation, Jev client timeout30초를 유지한다. cascade transport 오류를 Astra fallback 성공으로 바꾸지 않는다.
- U0f는 기존 동일 natural/주입 C 단독2셀을 같은 조건으로 한 번 수행한다. Astra20·U7각360은 기존 운영 점예측이며 강제되는 유한 호출 상한이나 충분시간 보장이 아니다. 단위 시작90% 투영, U7처럼 계획300초과 단위의 중간95% 조회 한 번, account/STOP/preflight 매 슬롯 및 기존 Jev append-only 비용 원장 규칙을 유지한다. U0f에는 중간 quota 조회가 없다.
- E5의 같은 source5 U0d 완료·재생 증거만 읽기 링크로 재사용한다. **E7 U0f는 E5 U0f를 링크하거나 완료로 간주하지 않는다.** 새 E7 U0f 실제 결과와 신규 playback-check가 있어야 E7 U7r0를 시작할 수 있다. U7r1은 새 E7 U7r0의 완전한 결과를 필요로 한다.

## 한 번의 확인과 종결 규칙

1. 조율자가 새 동결 전 source/payload/code SHA, 현 계정 fingerprint/plan/만료여유·quota window/reset 및 현재 r, 기존 infra proof의24시간/source/manifest/동시성3/current daemon 조건을 재확인한다. 새 source5 infra proof가 필요하면 기존 native 절차를 사용하며 과학조건은 바꾸지 않는다. 이 준비는 credentials·실시간 quota·Docker를 조회하지 않는다.
2. E7 U0f2셀을 정확히 한 번 동결·사전검사·실행한다. native2/2 valid strict admission을 충족하지 못하면 원 결과를 보존하고 **이 E7 계보 전체를 종결**한다. 같은 U0f를 성공할 때까지 반복하지 않는다. 통과는 해당 두 셀에서 경로가 다시 응답했다는 제한된 운영 증거이며 일반적인 제공자 안정성 보장은 아니다.
3. 통과 뒤 조율자의 독립 결과 확인 및 실제 위임 player 재생·pause/seek/end 확인을 신규 playback-check에 결속한다. 위임 변경기록 `05-delegated-review-amendment-20260927.md`에 따라 review_authority=delegated_agent, human_reviewed=false/deferred를 정직하게 유지한다. 실제 검토 전 played=true를 쓰지 않는다.
4. 위 가드를 충족한 뒤 E7 U7r0 전체36셀을 한 번 수행한다. 첫 invalid 시 형제 arm만 완료·보존하고 즉시 다음 슬롯을 막으며, 전체 E7를 종결한다. 이때 r1도 시작하지 않는다. 완전한 r0라면 같은 조건의 r1 전체36셀을 한 번 수행한다. semantic valid/failed는 등록 기준대로 분모에 남기며 인프라 invalid를 semantic 실패로 재분류하지 않는다.
5. E7 성공 여부와 무관하게 E6 실패/미시작·기존 source5/6/7 이력을 모두 유지한다. E6 성공 셀을 E7에 채워 넣거나 풀링하지 않고 실패 셀만 교체하지 않는다. 두 계보 중 성능이 좋은 결과를 주결과로 선택하지 않는다. 원 E6의 운영 실패와 E7의 추가 조건부 관측을 나란히 보고한다.
6. E7 두 반복이 모두 완전할 때만 native A/B/C 각 pass@1·pass@2·pass^2, 총9개 보조 지표를 E7 r1에 연결한다. N_i=2에서 pass@2는 과제별 적어도 한 번 성공, pass^2는 두 번 모두 성공이다. E6와 합쳐 N을 늘리거나 반복 신뢰도를 높이지 않는다. E7에 미실행·무효·누락이 하나라도 있으면 이 예정 반복 집계는 not-measurable다. 새 통계·기준·튜닝은 없다.

이 준비는 실제 회복을 미리 선언하지 않는다. 영수증과 해시 목록은 `codex-pre-freeze-20260927/remaining-u-preparation-20260927/budget-recovery-20260927/e7-preparation/`에 둔다. 원 E6 감사는 `e6-u7r0-audit/audit.json`, 오류 원인 감사는 `e6-u7r0-diagnosis/diagnosis.json`이다. 추가74셀에 의한 비용·사용량은 공통 원장에 더해지며 이전 unknown reserve·중단 상태를 지우지 않는다. 공개·실제 청구액·사람 검토 완료를 이 기록으로 주장하지 않는다.
