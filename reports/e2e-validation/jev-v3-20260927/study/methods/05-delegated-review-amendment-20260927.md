> Historical method/decision record; current findings and corrections are in the package index. Personal paths and account identifiers have been withheld.

# 부재 중 위임 검토와 실험·영상 종결 권한

기록 시각: 2026-09-27T17:52:50.315900+09:00

사용자 원문:

> 잠시 아버지 병문안 다녀올게. 다녀와서 쭉 체크를 할테지만 현재 영상-실험 양측 세션끼리 상황을 주고 받으며 예약된 롤아웃과 태스크들을 모두 닫을 수 있도록 해. 목표는 Jev에 관한 모든 실험이 종료되고 main에 병합 + 영상 완성이야. 품질이 떨어지지 않게 하고 토큰 사용량에 얽메이지 말고 작업을 계속 이어가. 다녀올게.

이 지시는 기존 병합 보류를 해제하고 feature → develop → main의 CI 검증된 merge commit 경로를 승인한다. 패키지 릴리스나 추가 외부 공개를 의미하지 않는다.

사용자가 돌아온 뒤 직접 확인하겠다고 하면서 그동안 모든 예정 태스크를 계속 닫도록 명시했으므로, 이 기록 이후의 U0f → U7 및 새 소스 U0c → U6b 진행에 한하여 05 §4.3·§8.1, playback 체크리스트의 인간 발급 조항 및 I5 protocol.md의 human playback 선행 조항에 있는 **사람 재생 검토 선행 시점**을 위임 검토로 변경한다. 사람이 이미 보았다는 사실을 만들지 않는다. 기존 동결 실행기·입력·분석·원결과·승인 영수증은 변경하지 않는다.

진행 조건은 같은 소스 admission strict 전수 성공, 전체 원자료 및 해시 독립 대조, 실제 파생 player의 재생·일시정지·탐색·끝 확인이다. 이 동작을 수행한 agent만 `played: true`를 발급하며, `review_authority: delegated_agent`, `human_reviewed: false`, `human_review_status: deferred_until_user_returns`, 사용자 승인·독립 검토·player 관측 영수증 해시를 함께 기록한다. 프레임 추출이나 렌더 준비만으로 played를 발급하지 않는다. `score_authority: false`를 유지한다.

05 관측 복구 변경 기록의 540/570/1290초, 반복·6셀1회, 모델·effort·입력·순서 및 새로운 소스 admission 2/2 조건은 유지한다. 원래 실패/무효/미실행 결과를 성공으로 바꾸거나 조건을 만족할 때까지 반복하지 않는다.

이 변경은 원래 인간 검토 설계와 구분되는 운영상 위임이며 최종 보고와 영상 provenance에 명시한다. 최종 사용자의 직접 검토 완료는 별도 사실로만 기록한다.

승인 원문 영수증: `[local-path-withheld]
