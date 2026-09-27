> Historical method/decision record; current findings and corrections are in the package index. Personal paths and account identifiers have been withheld.

# 01 · 환경·통합 검토: Jev primitives의 develop 통합과 Harbor E2E 준비도

- 작성: 2026-09-26 16:55 KST, 환경·통합 리뷰어. 읽기 전용으로 진행했고 git 쓰기, 모델 호출, Harbor 실행은 없었다.
- 대상: `codex/jev-primitives-20260925`@`d5d82ca2`와 develop `48ada6ba`(지시 기준). 검토 중 다른 세션의 fetch로 develop이 `04951699`(#3440: `/login` 리로드, 인증 문서)로 전진했다. 두 기준의 결과는 같다.
- 반영한 사용자 결정: root는 GPT-6 Astra xhigh, Codex ChatGPT 구독이다(사용량 여유가 있는 다른 계정으로 로그인).

## 판정

조건부 가능하지만 현재는 트리거할 수 없다. 통합 작업 자체는 기계적이다. 텍스트 충돌은 생성 파일 4개뿐이고, Jev의 production 파일은 develop과 겹치지 않는다. 병합 트리에서 Jev Python 12개 파일의 참조 심볼과 monkeypatch 대상도 누락이 0이다. #3435 라우팅 소유자, #3437 쓰기 진입 검사와 `.owner` 규칙, #3438 `transform_schema`, usage 필드 확장 모두 Jev matched adapter와 checker 계약을 깨지 않는다(#3438은 Anthropic 전용이라 Astra 경로와 무관하다). 확정된 root는 현 코드의 고정값과 정확히 맞는다. runtime, handoff, verifier, candidate, checker가 모두 `openai/subscription/gpt-6-astra/xhigh`로 고정되어 있다. 새 계정의 `[local-path-withheld] 파일 저장이고 토큰도 유효해(약 231시간 여유) Harbor 컨테이너 업로드 경로를 그대로 쓸 수 있다. 막히는 지점은 세 가지다. 새 소스로 돌릴 runner가 없고(B1), Score에는 실행 경로가 없으며(B2), Noul에는 4조합 workload와 정답이 없다(B3). 이와 별도로 quota 실측, 병합된 develop SHA 동결, Harbor-SDK 스키마 테스트, 비용 가드는 트리거 전에 반드시 끝내야 한다. 권장 순서는 통합 PR → develop SHA 동결 → Choice runner 재고정과 모델 없는 infra proof → quota 스냅샷 → 작은 admission이다. Score와 Noul은 B2·B3가 해소될 때까지 제외한다.

## 분류된 간극

| ID | 분류 | 간극 | 근거 | 수정 제안 |
|---|---|---|---|---|
| B1 | BLOCKING | 새 소스로 실행할 runner가 없다. r2 runner는 SOURCE worktree가 삭제되어 import 단정에서 즉시 실패하고, intent runner는 `a5b23bdc`에 고정되어 있다 | `.geode/eval-runs/jev-verdict-20260923-r2/runner.py:18,36-39`; `.geode/eval-runs/jev-intent-harbor-20260924/runner.py:29-30,83` | 병합된 develop SHA로 새 run 폴더를 만들고 run-spec 절차로 재고정한다. oracle 사본 `tests/handoff_runtime.py`가 양쪽에서 바뀌었으므로 task-bundle과 checksum도 재생성한다 |
| B2 | BLOCKING(Score) | `MatchedCandidateAdapter`는 테스트에서만 쓰인다. handoff primitive는 choice/noul만 받고, checker는 handoff에서 `candidate_judge`를 거부한다 | `evals/benchmarks/decision_candidate.py:45`; `evals/platforms/harbor_handoff.py:92`; `scripts/eval/check_harbor_observations.py:181-195` | 별도 PR로 추가한다: 후보 풀을 한 번 생성·해시해 공유하는 selector runner, best_of 전용 profile, checker의 purpose/route 확장, 독립 oracle |
| B3 | BLOCKING(Noul) | 코드 경로는 있지만 4조합(양쪽 true 포함) workload와 조건별 정답이 없다 | fixture 없음; `tests/scripts/test_check_harbor_observations.py:1806-1810`은 a0/a/b만 다룬다 | 4조합 injected candidate와 조건 라벨을 동결하고 noul real-Harbor 케이스를 추가한다 |
| R1 | REQUIRED-BEFORE-TRIGGER | 충돌 4건, 모두 생성물이다: `AGENTS.md`, `docs/architecture/extensibility-roadmap.md`, `site/src/data/geode/architecture-baseline.json`, `site/src/data/geode/changelog.ts` | `git merge-tree` 결과 | develop 쪽을 채택한 뒤 `uv run python scripts/architecture_baseline.py --update`와 `site/scripts/sync-stats.mjs`로 재생성한다 |
| R2 | REQUIRED-BEFORE-TRIGGER | worktree에 체크아웃된 hygiene 스크립트(d5d82ca2)에는 `assert-write-workspace`가 없어 exit 2로 거부된다 | d5d82ca2 `scripts/check_repo_hygiene.py:478-483` ↔ develop `:481-490,507`. develop 버전으로 실측하면 exit 0 | 병합 전에는 develop 버전을 stdin으로 실행한다(`git show origin/develop:scripts/check_repo_hygiene.py \| python3 - assert-write-workspace`). `.owner`는 추가만 한다. `task_id`는 바꾸지 않고, `session`/`session_id` 키도 새로 넣지 않는다(`_owner_metadata`는 마지막 값을 쓴다, `:315-329`). shlex로 파싱되는 `takeover_*=` 줄만 추가한다 |
| R3 | REQUIRED-BEFORE-TRIGGER | 로컬에서 통과한 후보는 통합 소스가 아니다 | `.agents/skills/geode-workflow/references/verification-gates.md:150-153` | Jev PR이 exact-head CI를 통과하고 병합된 뒤, fetch한 develop SHA로 동결한다. CI 복구 예산 3회를 감안해 첫 push 전에 전체 게이트와 site build를 돌린다 |
| R4 | REQUIRED-BEFORE-TRIGGER | Harbor-SDK 스키마 테스트 4건이 로컬에서 skip되었고 CI Harbor job도 이를 실행하지 않는다 | `tests/scripts/test_check_harbor_observations.py:551,1809`; `.github/workflows/ci.yml:339-354`(`test_harbor_docker.py`만 실행) | harbor 0.22.0 환경에서 로컬로 실행하고 noul 케이스를 추가한다 |
| R5 | REQUIRED-BEFORE-TRIGGER | 새 Codex 계정의 quota가 검증되지 않았다. GEODE는 구독 호출을 세지 않고 선언 한도만 보여 주며, 실측 함수는 호출하는 곳이 없다 | `core/cli/commands/login.py:348`; `core/llm/codex_oauth_usage.py:76,288` | 사용자 승인을 받은 뒤 WHAM usage를 한 번 조회하거나 Codex `/status`를 확인해 5시간·주간 used%와 reset 시각을 freeze에 기록한다. 중단 기준을 동결하고, 실행 중에는 같은 계정으로 대화형 Codex를 병행하지 않는다 |
| R6 | REQUIRED-BEFORE-TRIGGER | 컨테이너는 토큰을 갱신하지 못하고(파일을 다시 읽을 뿐이다), 실행 중 계정이 바뀌어도 감지하지 못한다 | `core/auth/codex_cli_oauth.py:142-144`; `evals/platforms/harbor_runtime.py:202-216` | trial마다 시작 전에 만료 여유(1시간 이상), `sha256(account_id)` 앞자리, plan claim을 private receipt에 기록하고 값이 바뀌면 중단한다 |
| R7 | REQUIRED-BEFORE-TRIGGER | 루프 비용 가드가 꺼져 있다(`cost_limit_usd=0`). TypeSafe 호출은 실제로 과금된다 | `evals/platforms/harbor_handoff.py:315`; verification-gates.md:162-165 | host 범위에 Jev 전용 원장(예약·상한)을 둔다. 구독 사용량은 0원으로 적지 말고 quota %로 기록한다 |
| R8 | REQUIRED-BEFORE-TRIGGER | 동결 이미지가 로컬에 없고, infra proof는 24시간이 지나면 만료된다 | `docker image inspect` 결과 No such image; r2 `runner.py:401-407` | 트리거 당일에 모델 없는 infra proof를 돌린다: 이미지 pull, verifier egress 차단, daemon identity |
| R9 | REQUIRED-BEFORE-TRIGGER | 실제 SDK가 직렬화한 요청에 대한 offline wire preflight를 아직 하지 않았다 | verification-gates.md:145-148 | Choice·Noul 각 arm의 실제 요청 bytes를 offline transport에서 검사한다 |
| R10 | REQUIRED-BEFORE-TRIGGER(결정 종속) | v2 계약(확률 반환, 합 허용 0.025, cascade)과 코드가 다르다. 허용오차는 production과 함께 쓰는 parser에 있다 | `core/llm/adapters/typesafe.py:217,228`(abs_tol=1e-5); 공유 호출처 `core/agent/verify.py:890`, `core/agent/loop/_reflection.py:542` | 채택한다면 eval 전용 validator로 분리하거나, production 변경임을 테스트와 함께 명시한다 |
| F1 | FOLLOW-UP | CI Harbor job에 observation 스키마 테스트가 없다 | `ci.yml:339-354` | `-k real_harbor`를 추가한다 |
| F2 | FOLLOW-UP | host Harbor venv가 lock과 다르다. anthropic 1.7.0/openai 2.54.0인데 lock은 0.116.0/2.45.0이고, editable `.pth`가 옛 worktree를 가리킨다 | `harbor-022/lib/python3.12/site-packages`; `pyproject.toml:25,51` | `PYTHONPATH=SOURCE`와 모듈 origin 단정을 유지하고, 다음에 venv를 재구성할 때 lock에 맞춘다 |
| F3 | FOLLOW-UP | host `[local-path-withheld] 만료된(−1517시간) GEODE 측 openai-codex OAuth 레코드가 남아 있다. 컨테이너와는 무관하지만 host에서 갱신되면 Codex CLI 로그인보다 우선한다 | `core/llm/providers/codex.py:109-205` | 정리하거나, host 측 점검 결과를 해석할 때 주의한다 |
| F4 | FOLLOW-UP | 업로드되는 auth.json 바이트가 고정되지 않는다. 실행 중 Codex 앱이 파일을 다시 쓸 수 있다 | `codex_cli_oauth.py:31-35`(`$CODEX_HOME`을 따른다) | 검증한 사본을 0600 권한의 trial별 `CODEX_HOME`으로 제공하고, dispatch env allowlist(r6 `runner.py:794`)에 추가한다 |
| F5 | FOLLOW-UP | `cache_write_1h_tokens`가 checker counters에 없다. Anthropic 전용이라 Astra와는 무관하다 | checker `:46`; `evals/platforms/harbor.py:144` | Anthropic root를 도입할 때 확장한다 |

## 근거 상세

### 1. 통합(merge-tree, 저장소 쓰기 없음)
- merge-base는 `2a074aae`이다. Jev는 ahead 3 / behind 137(`04951699` 기준 139)이고, diff는 20파일 +1791/−65이다. 양쪽이 모두 수정한 파일은 7개다.
- `git merge-tree --write-tree`는 scratch object dir로 실행해 저장소를 바꾸지 않았다. 충돌 4건, 자동 병합 3건이다. 자동 병합된 파일은 `CHANGELOG.md`(Jev 항목이 Unreleased L117로 들어간다), `official-docs-generation.md`, `decision_handoff_runtime.py`이다.
- develop이 제거한 `disable_settings_drift`(280dbd9f)는 병합 트리에 하나도 남지 않는다. `run_arm`은 `source="subscription"`, `effort="xhigh"`를 그대로 유지한다(`decision_handoff_runtime.py:1308-1318`). 이 파일의 줄 번호는 병합 트리 기준이다.

### 2. 의미적 상호작용
- #3435·#3429: 쿼터 소진이나 만료가 PAYG fallback을 허가하지 않는다(`core/llm/routing.py:152`). Score judge는 `infer_source(provider, model=)`를 쓰도록 바뀌었다(`core/agent/candidate_sampling.py:197-199`). `openai-codex` 설정값은 여전히 구독 route로 매핑된다(`core/llm/registry.py:265`).
- judge와 reflection prompt에 이전 task context가 추가되었다(`core/agent/verify.py:313,391`). 그래도 matched verifier는 요청을 자체 state로 교체하고(`decision_handoff_runtime.py:710-770`), 마지막 메시지 형식도 바뀌지 않아(`verify.py:629`) `:724` 단정은 유지된다. 대신 root 측 prompt가 길어지므로 옛 cohort와 합산할 수 없고, 180초 예산은 admission에서 확인해야 한다.
- usage: `cache_write_1h_tokens`가 `core/llm/adapters/base.py:199`와 `harbor.py:144`에 추가되었고 activity schema는 v11이 되었다. checker는 부분집합 검사만 하므로 호환된다(`:146`, `:300-316`). judgment 기본값은 `llm`이라(`core/config/session.py:30`) `run_arm`의 전역 Jev 금지 단정(`:1159`)도 통과한다. #3438의 production 변경은 `_anthropic_common.py:429-446` 한 곳이다. eval 계약(`scripts/eval/contract.py`, `docs/eval`)은 base 이후 변경이 없다.

### 3. Harbor 환경
- Harbor는 0.22.0으로 고정되어 있다(`harbor_runtime.py:154`, `harbor_docker.py:61`). agent는 `evals.platforms.harbor_handoff:GeodeHandoffHarborAgent`이고, native `GeodeRuntimeHarborAgent`를 상속하며 OpenAI 구독만 허용한다(`:166-167`).
- 컨테이너 `config.toml`은 모든 역할을 gpt-6-astra로 두고 `openai_credential_source="openai-codex"`, `anthropic_credential_source="none"`으로 설정한다(`:248-256`). env는 `:293-307`, allowlist는 `:261`에 있다. Anthropic PAYG root는 이 경로에서 불가능하지만(`harbor_handoff.py:252`의 `*API_KEY` env 금지 포함), 이번 결정으로 필요가 없어졌다.
- Jev 키는 owner-only 파일로 업로드되고(`harbor_handoff.py:114-127`) 로드 뒤 삭제된다(`:323`). `jev-1.13.0`은 공식 문서에서 여전히 current이다(09-26 확인).
- 네트워크: agent는 public이다(PyPI와 Python 설치, `chatgpt.com/backend-api/codex`, `api.typesafe.ai`). verifier는 정적 no-network이다. 로컬 환경은 Docker Desktop 29.0.1(aarch64, 8 CPU, 8 GB)이고, venv는 `[local-path-withheld]
- 필요한 자격 파일(이름만, 모두 0600): `[local-path-withheld], `[local-path-withheld]), run 폴더 `private-secrets/`의 trial별 임시 키.

### 4. Codex 구독 경로 준비도
- 위치: `$CODEX_HOME/auth.json`을 먼저 보고, 없으면 `[local-path-withheld] 쓴다. host의 `CODEX_HOME`은 설정되어 있지 않다. Codex `config.toml`에 `cli_auth_credentials_store`가 없으므로 파일 저장이다. `auth.json`은 09-26 08:20에 다시 쓰였고, 이는 재로그인 시점과 맞는다.
- GEODE 검증: `access_token`과 `refresh_token`이 필수이고, 만료는 JWT `exp`로 판단하며 없으면 `last_refresh`+1시간을 쓴다(`codex_cli_oauth.py:68-104`). 빌린 profile은 `openai-codex:codex-cli`이다(`core/wiring/container.py:257-268`). 만료된 토큰은 거부한다(`providers/codex.py:187`). 쿼터가 소진되면 `BillingError`로 실패하고 대체 경로로 넘어가지 않는다(`dispatch.py:583`).
- 실측(비밀값은 출력하지 않음): `auth_mode=chatgpt`, API key 필드는 null이고 토큰 4필드가 모두 있다. 만료까지 약 231.5시간 남았고 마지막 refresh는 8.5시간 전이다. plan claim은 `prolite`이며, JWT 계정 claim이 `tokens.account_id`와 일치한다.
- 컨테이너 사용: 설계상 가능하다. 파일을 `$HOME/.codex/auth.json`(0600)으로 업로드한다. 조건은 네 가지다: 파일 저장 방식 유지, 만료 여유, 모든 trial에서 같은 계정 사용(R6), 쿼터(R5). host의 `auth.toml`과 GEODE `/login openai` 토큰은 컨테이너로 넘어가지 않는다.

### 5. 이전 runner 가정 중 더 이상 맞지 않는 것
- SOURCE가 삭제되었다(B1).
- oracle 해시와 task-bundle 사본이 바뀌었다(`r2:259,315-317`).
- `rule_based`를 요청해도 실제로는 `llm_judge`로 동작한다(`verify.py:158-168`). intent runner(`:367-375`)는 이미 이를 반영했다.
- `validate_observations`에 `verification_primitive`가 전달되지 않는다(`r2:696-709`).
- runner가 첫 invalid에서 멈추므로(`r6:841`) 쿼터 오류가 나면 attempt가 소모된다.
- TypeSafe 키 경로(`r6:506-513`)는 여전히 유효하다.

### 6. 위임 반환
- 변경한 revision은 없다. 브랜치, worktree, `.owner`를 건드리지 않았고, 저장소 밖 scratch 임시 파일은 종료 시 삭제한다.
- 실행한 검사: `d5d82ca2`를 `48ada6ba`·`04951699`와 비교한 `merge-tree`, 정적 import 검사, `assert-write-workspace`(develop 버전 exit 0, worktree 버전 exit 2), 자격 메타데이터, `docker info`.

### 7. 정정 (2026-09-26 18:55, Build-A)
§3의 Harbor host venv 경로를 `[local-path-withheld] 정정한다.
- 근거: 기존 Jev Harbor 실행의 `host-environment.json` 7건이 모두 이 interpreter를 기록했다.
- 이 venv의 구성: `harbor 0.22.0`, `anthropic 1.7.0`, `openai 3.16.2`이고 pytest는 없다.
- 이 보고서가 처음 적은 `geode-jev-inbox-20260922/harbor-022`는 기록된 실행이 없는 보조 venv다.
- Harbor-SDK 테스트는 `uv run --offline --with harbor==0.22.0 python -m pytest ...`로 돌렸고 통과했다.
