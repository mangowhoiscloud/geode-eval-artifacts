> Historical method/decision record; current findings and corrections are in the package index. Personal paths and account identifiers have been withheld.

# Jev 실험 데이터 런북: 롤아웃에서 공개 trajectory까지

2026-09-26 · 데이터 파이프라인 담당 · 기준 `origin/develop` `48ada6ba`, Jev worktree `d5d82ca2`(develop 대비 137 behind / 3 ahead, 미병합). 조사 중 `origin/develop`이 `04951699`(#3440, 인증 후속)로 전진했으나 인용 파일은 바뀌지 않았다. 읽기 전용 조사이며 실행·업로드·유료 호출은 없었다.
표기: **[D]** develop 코드, **[W]** worktree 전용, **[P]** 비공개 run 디렉터리(`.geode/*` gitignore, `.gitignore:106`), **[A]** geode-eval-artifacts. 루트는 확정값 `gpt-6-astra` / Codex subscription / `xhigh`.

## 0. 판정 요약

| 대상 | develop 상태 | 첫 호출 전 필요 |
|---|---|---|
| Choice(intent·target helper) | Harbor 경로 있음 | [P] intent runner 재핀, 타이밍 필드 수정 |
| Noul(matched verifier) | 코드 없음 | [W] 병합, 2×2 셀·조건 정답 설계 |
| Score(best_of 선택) | 런타임·runner·oracle 없음 | 신규 구현 |
| Verdict panel(M7)·M8 | Choice 단일 라벨 어댑터만 | panel·지표·확률 계약 구현 |

## 1. 단계별 런북

| 단계 | 명령·함수 | 출력 | 체크 |
|---|---|---|---|
| S0 소스 동결 | [W]→develop PR→main 후 `git archive --format=tar.gz <rev> -- .geode core evals evolve scripts pyproject.toml uv.lock GEODE.md README.md README.ko.md CHANGELOG.md LICENSE NOTICE` | `source.tar.gz` | clean tree, pax comment=rev, `_verify_bundle`(harbor_runtime.py:107), `harbor==0.22.0`(:155) |
| S1 태스크 | [P] `make_tasks.py`; [D] `_task`(harbor_handoff.py:28), `validate_inbox_case`(decision_handoff_runtime.py:117), `validate_verification_intervention`(:184) | `payloads/<case>.json`, `task-bundle/` | payload sha=`--task-sha256`, instruction==request(harbor_handoff.py:134), image `@sha256`, verifier `no-network`, oracle 바이트=소스 |
| S2 무모델 증명 | [P] `--self-test`, `--self-check`, `--infra-preflight --reviewed` | `infrastructure/proof.json` | `model_dispatches=0`, 24시간 이내, verifier egress 차단 |
| S3 freeze | [P] `--phase <p> --freeze <bundle> --reviewed`; [D] `uv run python scripts/eval/contract.py validate-run-spec <p>/run-spec.json` | `run-spec.json`, `freeze.json`, `host-environment.json` | prospective·frozen, `live_test_approved=true`, workload hash(contract.py:557-561) |
| S4 preflight | [P] `--phase <p> --preflight` | 재해시 | natural은 admission 통과+`playback-check.json` 필수(r2 runner.py:354-375) |
| S5 실행 | [P] `--phase <p> --execute --reviewed` → 셀별 `Trial.create(TrialConfig(agent=AgentConfig(import_path="evals.platforms.harbor_handoff:GeodeHandoffHarborAgent", model_name="gpt-6-astra", override_timeout_sec=210, override_setup_timeout_sec=600, kwargs=…)))`(r6 runner.py:530-544). 컨테이너: `python -m evals.platforms.harbor_handoff --arm … --task … --task-sha256 … --revision … --timeout 180 [--verification-engine llm\|jev]` → `run_arm` | 아래 표 | 직렬, watchdog 930s, 첫 invalid에서 중단(r6 runner.py:841), Jev 키 파일은 셀마다 생성·삭제(:506-527) |
| S6 trial 수집 | [D] `uv run python scripts/eval/check_harbor_observations.py <trial> --run-spec … --run-spec-sha256 … --source-sha256 … --trial-name … --task-name … --task-checksum … --handoff-arm … --handoff-case-sha256 … --source-db <trial>/agent/geode-home/projects/-workspace/sessions/sessions.db [--expected-effective-verify-mode llm_judge] [--verification-engine llm\|jev]` | `observation-check.json`, `replay-check.json`, `cleanup-observation.json`, `trial-receipt.json` | **exit 2+`observation_valid=true`가 통과**, exit 1은 실패(:1199-1201). WAL 0바이트(:257). reward==verifier.passed==runtime.passed |
| S7 attempt | [D] `contract.py validate-attempts <p>/attempts.jsonl` | 셀당 1행 | 연속 sequence, evidence sha |
| S8 분석 | [D] `contract.py validate-analysis <p>/analysis.json --run-spec … --attempts …`, `contract.py validate-run-bundle <p>/run-spec.json` | `results.json`, `analysis.json` | invalid 선택 시 primary `not-measurable`(:762), 분모=동결값(:772) |
| S9 독립 감사 | [P] `analysis-review/` | 감사 receipt | 관찰·oracle·집계 재계산 |
| S10 공개 투영 | 원본 `agent/geode-trajectory.json`(`content_policy="digest"`, trajectory.py:537·647). 필요 시 [D] `geode session export-trajectory <session> --sessions-dir <trial>/agent/geode-home/projects/-workspace/sessions --digest-content --out …` | `review_state="reviewed"` 투영본, retrospective 공개 sidecar | `verify_trajectory_integrity`(:465). digest본은 항상 replay-incomplete(:441-462) |
| S11 릴리스 | [D] `geode session stage-trajectory-release <files> --destination <stage> --source geode-jev --scope <run_id> --privacy-review review.json --source-artifact REF=PATH --allow-replay-incomplete`, `geode session verify-trajectory-release <dir> --expected-manifest-sha256 <sha>`, `contract.py validate-publication <pub>/publication-manifest.json` | `trajectories/<source>-<scope>-<utc>-<sha12>/`, manifest `prepared` | reviewed 필수(trajectory_release.py:117-124), secret scan 0, 덮어쓰기 거부(:206), 저장소 URL 고정(contract.py:961) |
| S12 PR·read-back | 새 브랜치에 `public` 항목만 복사 → PR → merge commit → merge SHA에서 전 파일 바이트·raw API 앵커·`verify_trajectory_release`·`validate_publication` 확인([P] `verify_remote_readback.py` 패턴) | `remote-readback.json`, GEODE 레저에 merge SHA | 스쿼시 금지, 파일 수·바이트 일치 |

### trial 산출물과 파이프라인 차이

| 파일 | 생산자 | 등급 |
|---|---|---|
| `agent/geode-home/projects/-workspace/sessions/sessions.db`(+wal/shm) | AgenticLoop timeline, 경로=`handoff-result.json.db_path` | withheld-private |
| `agent/{session-events,call-events,handoff,verification,intervention,runtime-metadata}.json`, `trajectory.private.json` | `run_arm`(decision_handoff_runtime.py:1498-1566) | withheld-private, 검수 필드만 투영 |
| `agent/geode-trajectory.json`(digest)·`.private.json`(full), `handoff-result`·`runtime-result`·`runtime-finalized.json` | harbor_handoff.py:339-396 | digest는 공개 후보, full은 withheld |
| `agent/trajectory.json`(ATIF), `recording.cast`, `recording.receipt.json` | 호스트 `populate_context_post_run`(harbor_runtime.py:367-427), harbor.py:546 | withheld-private |
| `result.json`, `verifier/{reward.txt,verifier-receipt.json}` | Harbor, 태스크 oracle | 투영 후 공개 |
| `trial-receipt`·`observation-check`·`replay-check`·`cleanup-observation`·`evidence-manifest.json` | [P] runner | 투영 후 공개 |

알려진 파이프라인과 다른 점:
- `sessions.db`, `call-events.json`, `session-events.json`은 `harbor_handoff`가 아니라 `run_arm`이 만든다.
- `run_arm`의 digest `trajectory.json`(:1513)은 호스트 ATIF가 덮어쓴다(harbor_runtime.py:426). 정본 digest는 `geode-trajectory.json`이다.
- Harbor 궤적은 단일 세션(harbor_handoff.py:347)이고 `review_state="local"`(:353)이다. CLI `export-trajectory`도 단일 세션이며 id가 `geode-session-<id>`(typer_session.py:699, trajectory.py:746)라서 Harbor의 `harbor-<id>`와 다르다.
- ATIF·cast는 finalization 오류나 스냅샷 불완전이면 생기지 않는다. handoff는 replay가 불완전하면 예외를 낸다(harbor_runtime.py:384-401).
- trial 영수증, reward 대조, cleanup, playback 게이트, 공개 투영(normalize.py), read-back은 develop 밖([P]/[A])에 있다.

## 2. 디렉터리·명명·해시

```
.geode/eval-runs/jev-<primitive>-<study>-<YYYYMMDD>[-rN]/   # 0700
  protocol.md runner.py make_tasks.py source.tar.gz
  payloads/<case_id>.json  task-bundle/{manifest.json,<case_id>/}
  infrastructure/proof.json
  private-secrets/          # 열람·해시·게시 금지
  <phase>/ run-spec.json freeze.json host-environment.json dispatch-lock.json
           trial-starts.jsonl child-NNN.log trials/<trial_name>/
           results.json attempts.jsonl analysis.json [playback-check.json]
           tables/          # §5 파생 뷰(신규)
  analysis-review/
  publication/{privacy-review.json,normalization-receipt.json,publication-manifest.json}
```

| primitive | 디렉터리 | phase(셀) | arm·플래그 |
|---|---|---|---|
| Choice | `jev-choice-intent-*` | admission 2(inbox-admission A,B) → natural 6(3 inbox×2 arm×1회) | runtime arm `a`(Astra helper)/`b`(Jev helper), `verify_mode=rule_based`(실효 `llm_judge`) |
| Noul | `jev-noul-verdict-*` | admission → conditions(모순×근거부족 4조합×2 engine×R) | `a0`+`verification_engine`+[W] `verification_primitive=noul` |
| Score | `jev-score-bestof-*` | pool(1회 생성·동결) → admission → selection(같은 pool×2 selector) → continuation | profile 미구현 |
| Verdict panel | `jev-verdict-panel-*` | build → selection → test → stability. Harbor 없음, [P] M5 snapshot runner 패턴 | `MatchedVerifierAdapter` 직접 호출 |
| M8 E2E | `jev-verdict-e2e-*` | admission → natural → injection | `a0`+engine, C cascade 미구현 |

명명: `run_id=geode-jev-<primitive>-<phase>-<YYYYMMDD>[-rN]`(`^[a-z0-9][a-z0-9._-]{2,127}$`). `trial_name=<prefix>-<phase>-r<rep>-<case_id>-<arm>`, `attempt_id=<run_id>-a<NNNN>`, 집계 행 `<run_id>-aggregate`. 재실행은 새 `-rN`과 lineage로 남기고 기존 파일은 `open('x')`로 불변 유지. 릴리스 scope는 run_id와 같게 둔다.

해시(SHA-256 hex): 파일 바이트(source.tar.gz, payload=`case_sha256`, fixture, uv.lock, oracle, task-bundle, run-spec, attempts, results). `workload_ids_sha256=sha256(json.dumps(ids, ensure_ascii=False, separators=(",",":")))`. 판정 `input/question/feedback/raw_answer_sha256`은 정렬 canonical JSON(`_digest`, `_json_digest`). `task_checksum`은 Harbor `Task.checksum`. 릴리스 디렉터리 접미사는 manifest sha 앞 12자.

## 3. 첫 호출 전 동결

- **소스·환경**: main 승격 rev, bundle sha(=git archive), uv.lock, Harbor venv(`[local-path-withheld], 0.22.0)와 `host-environment.json`, Docker daemon, image digest, agent public/verifier no-network, infra proof.
- **워크로드**: payload·task checksum, 셀 순서·회전·trial_name, 반복 수, admission 분리, replay 쌍 사전 선택.
- **경로**: root·reflection·final·replan은 `gpt-6-astra`/openai/subscription/xhigh, Jev는 `jev-1.13.0`/typesafe/payg/effort `none`. 전역 `judgment_engine=llm`(decision_handoff_runtime.py:1157). `llm_max_retries=1`, `cost_limit_usd=0`, fail-fast(harbor_handoff.py:286-294), env API 키 금지(:237). 180s/6 rounds, Harbor 210/600/30s, watchdog 930s, cleanup 120s, trial 재시도 없음.
- **판정 계약**: `question_sha256`(Choice `_QUESTIONS`, Noul `_NOUL_QUESTIONS`, Score `CANDIDATE_LEVELS`), 확률합 허용오차, Noul `p≥0.5`와 우선순위(모순>근거부족>supported), Score pool(2–4개, 각 ≤2,000자, 입력 순서=동점 규칙, attempt inventory), 개입 바이트, Noul 셀별 조건 정답.
- **분석**: primary(name·unit·direction·aggregation·denominator), strict success, invalidation·analysis plan, 전 계획 셀 `selected_for_analysis=true`, `PRICE_REFERENCE`(checked_at 2026-09-21: Jev input $0.042/M·output $0, Astra input $10·cached $1·cache-write $12.5·output $50 per M, ≤272K), budget, privacy boundary.
- **패널(M7)**: 항목과 gold(수집 전 withheld-sealed), source task 단위 split 해시, stability subset, τ 규칙, bootstrap 2,000회와 시드.

## 4. invalid·fallback·unknown

| 상황 | 분류 | 성공 집계 |
|---|---|---|
| Jev 키 없음. 전역 route는 LLM을 유지한다(judgment.py:15-35, `missing_jev_key` :47-50) | Jev arm 호출이 Astra로 기록되면 route 불일치(check_harbor_observations.py:181-193) → invalid, 중단. matched 경로는 키가 없으면 실행 전에 실패(harbor_handoff.py:304) | **Jev 성공 아님** |
| Score judge 실패 → 후보 0 fallback(candidate_sampling.py:242-261) | 선택 미승인([W] decision_candidate.py:51). invalid 또는 selector valid-failed 중 하나로 동결 | 과제가 통과해도 선택 성공 아님 |
| 완료된 Jev 응답이 형식 불합격 | Choice helper는 tool error이며 우회 금지 → valid failed(typesafe-decision-handoff.md:429). 판정은 `verification_error` hold(:124). 패널은 오답 | 실패 |
| 전역 판정의 Jev 형식 불합격 | `invalid_jev_response`·`verification_error` hold, LLM 재판정 없음(verify.py:889·914-920) | 실패 |
| transport 오류, route drift, usage 누락·모순, 관찰 체크 실패, export 불완전 | `validity=invalid`, `outcome=unknown`, `failure_class` 필수 → 중단 | primary `not-measurable` |
| 의미적 실패(oracle fail, hold, 오판) | valid/failed | 분모 포함 |
| admission | 별도 run_id·디렉터리 | natural 분모 제외 |

Unknown 규칙:
- 토큰·캐시·추론 누락은 `null`이고 0으로 바꾸지 않는다. 합계는 전 호출이 관측될 때만 낸다(`_aggregate_accounting` :1591). 부분값은 `*_observed_sum`과 `missing_calls`로 둔다.
- `duration_ms ≤ 0`은 `null`로 읽는다. 저장 단계가 누락 지연을 0.0으로 채운다(activity_registry.py:298).
- `call-events.json`의 `cost_usd`는 출처 표시가 없는 tracker 추정이므로 비용 열에 쓰지 않는다.
- 실제 청구는 대조 전까지 `null`이다(`reported_cost_usd` :307, Harbor `cost_usd` harbor_runtime.py:382).
- invalid 셀도 선택 상태로 남겨 primary를 `not-measurable`로 만든다. 셀을 빼서 분모를 줄이지 않는다(validator는 분모 값만 비교, contract.py:772). 기술통계에는 valid 분모를 적는다.

## 5. 분석용 테이블(영상팀)

04 브리프 이름에 맞춘다: 호출=`call_ledger`, 시행=`e2e_trials`(판정 수준은 `judge_items`·`noul_items`), 쌍=`e2e_pairs`(신규), 요약=`primitive_summary`(`runs`의 arm 확장). 모든 행에 `run_id, phase, primitive, source_revision, source_ref, sha256`을 둔다. 단위는 토큰=정수, 시간=s(ms 변환), 비용=USD(Jev는 US cents 병기), 시각=ISO-8601 UTC, 확률=[0,1].

**비용 3종**(서로 더하지 않음, 루트 확정에 따라 PAYG 열은 두지 않음):
- `subscription_api_equivalent_estimate_usd`: Astra subscription 호출의 API 단가 환산. 캐시 세부가 없으면 null이고 `subscription_api_equivalent_bounds_usd`(low, high)만 둔다. 청구서가 아니다.
- `typesafe_price_estimate_usd` / `_us_cents`: Jev 공시 단가×`input_tokens`, output $0. `output_tokens`는 그대로 보존한다.
- `actual_billed_usd`: 대조 전 null, `billing_status`(unknown|reconciled), `billing_receipt_sha256`. 원천 `reported_cost_usd`는 현재 항상 null이다.
- Astra PAYG 호출은 동결 경로 위반이라 invalid이다. Jev의 `payg`는 route 표기이며 크레딧 차감은 `billing_status=unknown`에 속한다. `price_reference_date`와 `price_reference_source`를 함께 둔다.

**`call_ledger`**(1행=recorded attempt; `runtime-result.json.usage.recorded_attempts` ⨝ `handoff-result.json.call_accounting` ⨝ `call-events.json`, 키 `llm_attempt_id`)
- `trial_name, arm_label(llm|jev), session_id, llm_call_id, llm_attempt_id, source_event_id, purpose, role(root|reflection|final_judge|helper|selector), model, response_model, provider, route, effort`
- `occurred_at_utc, latency_s(=duration_ms/1000)`
- `input_tokens, output_tokens, cached_input_tokens, cache_write_tokens, cache_write_1h_tokens, reasoning_tokens, total_tokens(in+out, 모순이면 null), contradictory_usage`
- `error_type, response_id_sha256, accepted, verdict, probabilities_json, q_max, noul_p_contradiction, noul_p_missing, score_json`, 비용 3종

**`e2e_trials`**(1행=계획 셀, invalid 포함)
- `cell_index, case_id, repetition, position, arm_label, runtime_arm, verification_engine, verification_primitive`
- `validity, outcome, failure_class, error_type, execution_started, observation_valid, replay_complete, source_reconciled, cleanup_complete`
- `native_reward, verifier_passed, oracle_passed, native_final_verdict, strict_success, jev_decision_status(admitted|rejected|transport_error|fallback|n/a)`
- `judgment_attempts, replan_requests, root_requests_consuming_feedback, helper_invocations, lookup_attempt_count, extra_lookup_count, wrong_target_lookup_count, rejected_lookup_count, false_completion_count, judge_false_acceptance, held_delivery, repaired_success`
- `noul_pred_{contradiction,missing}, noul_true_{contradiction,missing}, score_pool_sha256, score_winner_index, score_winner_grade`
- `runtime_elapsed_s, host_elapsed_s, judge_latency_{sum,median}_s, helper_tool_s`
- route(astra, jev)별 `{input,output,cached_input,reasoning}_tokens_{total,observed_sum,missing_calls}`, 비용 3종의 `_total`·`_observed_sum`
- `trial_receipt_sha256, result_sha256, geode_trajectory_sha256, recording_cast_sha256, replay_preselected`
- (§5.1 반복 계약) `policy_digest, reset_digest, input_sha256, task_checksum, verifier_sha256`(`input_sha256`은 셀 `case_sha256`): `freeze.json` 셀 값, 없으면 private receipt의 같은 이름
- (05 v2 쌍 동시 실행, 2026-09-26 추가) `slot_id, dispatch_skew_s, agent_start_skew_s, pair_sync, concurrent_trials, external_account_usage`(항상 `"unknown"`): private receipt(`<phase>/private-receipts/<attempt_id>.json`)에서 투영. Run receipt 초안 이름(`pair_launch_skew_s, pair_agent_start_skew_s, concurrent_trials_active`)은 별칭으로 받고, 값이 다르거나 `pair_sync`가 30초 규칙과 모순이면 거부한다. `overlapping_calls`(+`_observed`, `_missing_intervals`)는 `call_ledger` 구간(종료 시각−지연)으로 다른 trial 호출과 겹치는 수를 사후 계산하며, 구간 누락이나 불완전 사용량이 있으면 null이다. 계정 지문 등 나머지 private 필드는 투영하지 않는다
- (05 §3.1 strict 규칙, 2026-09-27 추가, 통합 0020·0021) `strict_rule`(verdict|intent, 동결 셀의 `verification_engine` 유무로 정함), `strict_success_with_lookup`(두 규칙 모두 조회 조건 추가), `judgments_admitted, feedback_consumption_complete, false_completion`(matched 판정 기준, helper 셀은 null), `runner_strict_success`(runner receipt 값, 재계산과 다르면 export 거부), intent 셀의 `helper_admitted, helper_fallback_used, helper_feedback_consumed`(runner receipt 같은 이름, 없으면 `call_ledger` helper 호출과 oracle 소비 검사), `strict_unobserved`(관측 못 해 strict가 null인 사유). `strict_success`는 verdict 셀에 조회 조건을 넣지 않는다

**`e2e_pairs`**(1행=(case_id, repetition)의 LLM|Jev)
- `pair_complete, llm_trial, jev_trial, first_arm, llm_passed, jev_passed`
- `success_delta`(jev−llm, −1/0/1, 불완전하면 null), `runtime_s_delta, host_s_delta, judge_latency_s_delta`
- route별 토큰 차이, 비용 출처별 차이(양쪽 total이 있을 때만), `replay_selected`
- (05 v2, 2026-09-26 추가) `slot_id, same_slot, pair_sync`(둘 다 true일 때만 true), `dispatch_skew_s, agent_start_skew_s`(둘 중 최대), `intra_pair_latency_comparable`(완전·같은 슬롯·동기 쌍). 쌍 내부 지연 요약은 comparable 쌍만 쓰고, 성공·복구·비용 분석은 모든 쌍을 유지한다(05 v2 §3.6)

**`primitive_summary`**(1행=run×phase×arm, primitive 합계 행 포함)
- `planned_cells, attempted, valid, invalid, passed, failed, success_rate_valid`
- `primary_name, primary_value(number|"not-measurable"), primary_numerator, primary_denominator, independent_units`
- `median_{runtime,host,judge_latency}_s`(불완전하면 null), 사용량 total과 coverage, 비용 3종과 bounds
- `jev_contract_errors, fallbacks, admission_excluded=true, run_spec_sha256, analysis_sha256`
- (§5.1, `--reliability` 지정 시 arm 행만) `reliability_unit, reliability_pass_at_{n}, reliability_pass_hat_{n}, reliability_complete_tasks_n{n}, reliability_summary_sha256`

### 5.1 반복 신뢰도 보조 집계(2026-09-26 추가)

[05 §3.5](05-preregistration.md#35-반복-신뢰도-보조-분석v1)와 [06 원문·수식](06-reliability-lens.md)을 따른다. 새 원본 테이블 없이 기존 e2e_trials → primitive_summary/analysis.json의 보조 지표로 낸다.

- U7r0/r1의 case_id·arm·source_revision·policy/reset·입력/verifier hash가 같고, 두 반복의 계획 행렬이 완전할 때만 결합한다.
- 지표별 n, planned_tasks, complete_tasks, incomplete_tasks, expected_repetitions, observed_repetitions, valid_repetitions, run_spec_sha256s 및 원천 행 포인터를 남긴다. N<n·중복 rep·unknown·계약 불일치는 집계를 거부한다.
- 전체 시행의 strict_success로 pass@1, pass@2, pass^2를 계산한다. repair round, 질문 변형, 후보, replacement lineage를 독립 반복으로 세지 않는다. 동일 과제 집합의 A/B만 비교한다.
- U6b와 U8은 조건당 1회이므로 pass^2를 만들지 않는다. Score는 pool-random@1 / oracle-coverage@4 / selected success를 별도 열에 둔다.
- 원본 실패·무효·비용은 보존한다. 예정 반복이 불완전하면 예정 집계는 not-measurable이며 valid-only 수치로 대체하지 않는다.
- 구현 배치(2026-09-26 확정, 통합 담당 구현 중):
  - 계산식: `evals/benchmarks/decision_metrics.py`. `pass_at_n`, `pass_hat_n`, 반복 행렬 검증(거부 사유 열거)과 06 §7 검사 5종 테스트를 둔다.
  - 집계: `scripts/eval/handoff_tables.py`. `e2e_trials`를 (arm, case_id)로 묶고 계약 동일성을 확인한 뒤 `tables/reliability.jsonl`(과제×arm, 원천 행 포인터)과 `tables/reliability_summary.json`(arm×n, 출처 필드)을 쓴다. `primitive_summary`에는 보조 열로 붙인다.
  - 완전성 게이트: `scripts/eval/denominator_coverage.py`. 계획 대 관측, 중복, N<n, 계약 불일치, unknown이 있으면 non-zero로 거부한다. 집계보다 먼저 돈다.
  - `analysis.json`: 스키마를 바꾸지 않는다. 보조 지표는 `metrics` 행으로 둔다(value=평균, numerator=Σ과제별 비율, denominator=complete_tasks). `source_locator`는 `reliability_summary.json`을 가리키고, 측정 불가이면 value="not-measurable", numerator와 denominator는 null이다.
  - policy/reset digest: runner 소유 `freeze.json`에 셀별로 기록하고 `e2e_trials` 열로 가져온다.
    - 이름은 Run receipt 필드와 같은 `policy_digest`(route·effort·프롬프트·도구·verifier·예산·수정 한도)와 `reset_digest`(세션·파일·캐시 reset 경계)다. 계산 함수는 `decision_metrics.policy_digest`/`reset_digest`(2026-09-26 통합 담당).
- 이 배치는 구현이 끝나 테스트로 확인되기 전까지 완료로 보지 않는다.

## 6. GAP

| 등급 | 항목 | 근거 | 조치 |
|---|---|---|---|
| BLOCKING | Noul 없음 | develop harbor_handoff.py:86-96에 primitive 인자 없음, typesafe.py:1·126-145는 Choice 전용, checker main(:1146)에 플래그 없음. [W] harbor_handoff.py:81-93, decision_verification.py:69·337, check_harbor_observations.py:779·1208 | [W]→develop PR. dry merge 결과 코드는 자동 병합, 문서·사이트 4개 충돌(AGENTS.md, extensibility-roadmap.md, architecture-baseline.json, changelog.ts) |
| BLOCKING | Score 런타임·runner·oracle | develop에 decision_candidate.py 없음. [W] :45-51은 "Harbor runner 아님". handoff 도구 고정(harbor_handoff.py:141-143), checker 허용 purpose에 `candidate_judge` 없음(:181-193), 단일 세션 export(:347)라 best_of 자식 세션 누락 | pool 생성·동결, Score profile, 후보별 독립 oracle, checker profile, 다중 세션 export |
| BLOCKING | Verdict panel·cascade | evals/·scripts/eval/·core/에 Brier·ECE·AUROC·risk–coverage·cascade 없음(유일 hit skill_attribution_native.py:29는 무관). 판정 어댑터는 단일 라벨 | panel builder·gold·split, Astra 확률 계약, 지표·bootstrap, stability runner |
| REQUIRED-BEFORE-TRIGGER | runner 재핀 | develop에 Jev Harbor runner 없음. [P] intent runner.py:29-35가 rev `a5b23bdc`, 옛 worktree, r6 runner(sha `2c1b1427…`)를 고정. 이후 관련 7파일 변경(+155/−72) | 새 rev로 bundle·task·self-check 재생성 |
| REQUIRED-BEFORE-TRIGGER | 타이밍 필드 | [P] intent runner.py:748은 `latency_ms`를 읽지만 저장 payload는 `duration_ms`다(activity_registry.py:298, r2 trial 실측) | `duration_ms` 사용, ≤0은 null |
| REQUIRED-BEFORE-TRIGGER | Noul 2×2 | 개입은 `before/after_observation` 단일 후보뿐(decision_handoff_runtime.py:184-203). 둘 다 true인 셀과 조건 정답 oracle 없음 | fixture·셀·정답 동결 |
| REQUIRED-BEFORE-TRIGGER | 확률 허용오차 | develop typesafe.py:140, [W] :216-228 `abs_tol=1e-5`. JJ 기준은 0.025(jev-update-plan.md:21) | 값 동결 |
| REQUIRED-BEFORE-TRIGGER | reflection cadence·실효 verifier | 라운드마다와 최종 전 reflection(usage-accounting.md:299). helper 비교는 `--expected-effective-verify-mode llm_judge --source-db` 필수(typesafe-decision-handoff.md:21-35) | 호출 수 기준선 재측정, reflection coverage 검사 |
| REQUIRED-BEFORE-TRIGGER | Score fallback 분류 | [W] decision_candidate.py:51(invalid)과 helper 거부=valid failed(typesafe-decision-handoff.md:429)가 다름 | 하나로 동결 |
| REQUIRED-BEFORE-TRIGGER | 가격 참조 | `PRICE_REFERENCE` 2026-09-21(decision_handoff_runtime.py:32-56) | 재확인 후 날짜·출처를 run-spec에 동결 |
| FOLLOW-UP | 공개 투영기 | Harbor `review_state="local"`(harbor_handoff.py:353), stage는 reviewed 요구(trajectory_release.py:117-124). 투영 코드는 [A] normalize.py:348-420(@`f1d5f4ed`)에만 있음 | GEODE로 일반화, Noul·Score 필드 allowlist |
| FOLLOW-UP | 테이블 exporter | §5 테이블을 만드는 코드 없음 | 영수증 기반 결정적 exporter |
| FOLLOW-UP | 분모 검증 | validate_analysis가 선택된 valid 셀 수를 분모와 대조하지 않음(contract.py:646-785) | 검사 추가 |
| FOLLOW-UP | 청구 대조 | TypeSafe 요청별 청구 export 미확인 | response_id 대조 receipt, 그전까지 null |
| FOLLOW-UP | read-back 도구 | `verify_remote_readback.py`는 [P] 전용. manifest는 `prepared`로 커밋(contract.py:1008-1018) | 템플릿화 |

선행 프로세스 게이트: provider 배치의 최종 인계 전에는 Jev 통합과 유료 run을 하지 않는다(CLAUDE-HANDOFF.md §1).
