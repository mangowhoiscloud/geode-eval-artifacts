# GEODE vs native Codex on Terminal-Bench 2.1

Same model, different harness. Korean first, then English.

## Timeline

00:00 한국어
00:00 동일 모델, 다른 하네스
00:11 세 문장으로 먼저 답합니다
00:21 공통 셀에서만 직접 비교합니다
00:31 우세 태스크 수는 같았습니다
00:42 이 실행의 성취는 점수 하나가 아닙니다
00:53 하네스가 같은 모델의 성과를 바꾸는가?
01:03 Terminal-Bench 2.1은 실제 터미널 작업을 측정합니다
01:14 cell이 비교의 최소 단위입니다
01:25 공유 조건을 동결한 뒤 runtime만 갈랐습니다
01:36 Harbor가 trial을 격리하고 verifier를 실행했습니다
01:46 점수와 행동, 절차의 증거 권한이 다릅니다
01:56 원본 시도는 보충 실행 뒤에도 사라지지 않습니다
02:06 890개 의도 셀을 네 상태로 추적했습니다
02:16 +8셀은 paired outcome에서 직접 확인됩니다
02:26 평균은 반대 방향의 큰 태스크 효과를 숨깁니다
02:37 GEODE의 우세는 작고 태스크 의존적입니다
02:48 실패는 0점과 인프라 무효로 먼저 나뉩니다
02:59 영상 처리 태스크는 시간 예산 경계를 드러냈습니다
03:11 20개 셀은 모델 호출 전에 대칭 제외했습니다
03:24 native Codex의 6셀은 보충 한도 뒤에도 미해소입니다
03:35 890-cell 관찰 범위와 재생 가능 범위를 구분했습니다
03:46 공개는 raw 복제가 아니라 검증된 allowlist입니다
03:56 이 결과가 말하지 않는 것도 명시합니다
04:07 성능 우세보다 더 강한 성취는 검증 가능한 비교입니다

04:19 English
04:19 Same model, different harness
04:30 The result in three sentences
04:40 Direct comparison uses only exact-common cells
04:50 Task wins were evenly split
05:01 The accomplishment is more than one score
05:12 Does the harness change the same model's outcome?
05:22 Terminal-Bench 2.1 measures real terminal work
05:33 The cell is the smallest comparison unit
05:44 Shared conditions were frozen before runtime assignment
05:55 Harbor isolated each trial and ran the verifier
06:05 Score, behavior, and procedure have different authority
06:15 Original attempts remain after supplements
06:25 All 890 intended cells remain accounted for
06:35 The +8-cell edge is visible in paired outcomes
06:45 The mean hides large opposing task effects
06:56 GEODE's observed edge is modest and task-dependent
07:07 Failures first split into valid zeroes and invalid attempts
07:18 A video task exposed the time-budget boundary
07:30 Twenty cells were symmetrically excluded before model calls
07:43 Six native Codex cells remained unresolved after supplement caps
07:54 The 890-cell observation index is broader than replay coverage
08:05 Publication is a verified allowlist, not a raw dump
08:15 The result also states what it cannot establish
08:26 The stronger accomplishment is a verifiable comparison

## Evidence boundary

Harbor result and verifier receipts are score authority. Trajectories and derived casts are behavior evidence. Observer PTY and this film are procedure/presentation evidence. The full-suite primary is not measurable, and this is not an official leaderboard score.
