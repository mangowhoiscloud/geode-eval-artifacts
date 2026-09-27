> Historical method/decision record; current findings and corrections are in the package index. Personal paths and account identifiers have been withheld.

# X1 · CUAVerifierBench → Choice 완료 판정 (외부 검증 데이터)

- 작성: 2026-09-26~27, 외부 검증 데이터 담당(claude). 모델 호출 0회, Docker·Harbor 0회, 공유 GEODE 저장소 쓰기 0회. 네트워크는 Hugging Face의 이 데이터셋 API·카드·파일만 썼다.
- 권위: 사전 등록은 [05 §11](../../methods/05-preregistration.md)이다. 이 문서는 데이터·입력 계약·채점 정의를 적는다. 절 초안은 ../05-s11-external-draft.md (역사적 참조: `../05-s11-external-draft.md`; 해당 자료는 이 공개본에 포함되지 않음)에 있다.
- **runner 코드는 여기서 만들지 않았다.** Choice 단독 `PanelUnit`과 이진 채점은 통합 담당의 패치 0022 몫이다(2026-09-27 조율자 지시). §3·§4가 그 패치의 입력 계약과 채점 정의다.

## 1. 출처와 핀

| 항목 | 값 |
|---|---|
| 저장소 | Hugging Face `microsoft/CUAVerifierBench`(Microsoft Research AI Frontiers), 논문 arXiv 2604.06240 |
| revision | `c19eb323cd802add5c3d2840ff13044061364867`(lastModified 2026-04-21T19:30:05Z) |
| 접근 | `gated=false`, 로그인·동의 없음. 토큰을 쓰지 않았다 |
| 라이선스 | MIT(카드 YAML·본문). 카드 sha256 `44d7190b72ae489297f59d6fadff635ced6dd067c845c77b04f187a7b2d7bec7` |
| 구성 | config `trajectories`(과제당 1행, 스크린샷 포함)·`annotations`(과제×검토자 1행). split `fara7b_om2w_browserbase`(Online-Mind2Web 과제, Browserbase 실행)·`internal`(Microsoft 내부 heldout aurora-v2 과제) |
| 실측 규모 | 궤적 260(internal 154, om2w 106), 사람 판정 행 **369**(om2w 215 = 103과제×2 + 3과제×3, internal 154×1). 처음 추정한 629가 아니다 |

원천 파일(revision 고정, LFS sha256):

| 파일 | 크기(B) | LFS sha256 | 받은 방식 |
|---|---|---|---|
| `annotations/fara7b_om2w_browserbase-00000-of-00001.parquet` | 77,932 | `10d459cf76e888de082534be156f60974176617242ce5ebdaac554461468ab84` | 전체, sha256 대조 일치 |
| `annotations/internal-00000-of-00001.parquet` | 15,450 | `3741e6927bc1d2f1b346d346bbf7813561c44d24e80b9975451c7773b6fd21e4` | 전체, sha256 대조 일치 |
| `trajectories/fara7b_om2w_browserbase-00000-of-00002.parquet` | 461,305,772 | `00f6083c3465d9644a51ec6279d6bc13795375d2c5f6deb00e2322210076654a` | footer + 텍스트·라벨 열만 HTTP range |
| `trajectories/fara7b_om2w_browserbase-00001-of-00002.parquet` | 414,473,352 | `79b22396664658e548c2c0ef3e4e5b28760265cf701724bb6a1edae6ae47122e` | 같음 |
| `trajectories/internal-00000-of-00002.parquet` | 626,005,617 | `923ae24f2ff72fba6e43a7302f58fd374e1e53fef497ead70fc4b2cb345a522e` | 같음 |
| `trajectories/internal-00001-of-00002.parquet` | 732,069 | `aeb7de912a8e853df07c02a97f390849362872d7a8a56916241ccb135135c319` | 같음 |

- **스크린샷은 받지 않았다.** trajectories parquet은 footer와 필요한 열의 column chunk만 range 요청으로 읽었다. 받은 양은 2,028,026 B다(파일 합 1,502,516,810 B). `screenshots` 열은 요청하지 않았다.
- 한계: range로 읽은 trajectories 파일은 전체 sha256을 로컬에서 재계산할 수 없다. API의 LFS oid와 받은 범위마다의 sha256을 `fetch-receipt.json`(캐시)에 남겼다.
- 데이터 파일 다운로드 합계: 2,121,408 B(range 2,028,026 + annotations 93,382). 카드·API 응답은 따로 수 KB다.

## 2. 변환 규칙(모델 출력을 보기 전에 고정)

| 규칙 | 내용 |
|---|---|
| 분석 단위 | 궤적 1개 = 상태 1개 |
| gold | UV-blind `human_judgement_outcome`(Correct/Incorrect)의 **엄격 다수결**. `gold_accept = (다수 == Correct)`. informed 단계(UV를 본 뒤) 필드는 쓰지 않는다 |
| 동률 | 제외하고 `excluded.x1.jsonl`에 남긴다. **21건**, 모두 om2w의 2인 1:1 |
| 표본 | 표집 없음. 동률을 뺀 전부: **N = 239**(internal 154, om2w 85) |
| 입력 | 지시문, 행동 로그, 최종 답, 시작 URL·시각. 스크린샷·라벨·검증기 열은 넣지 않는다 |
| 길이 한도 | `len(json.dumps(state, ensure_ascii=False)) ≤ 60,000`. 매치된 판정기 E2E 경로의 상태 한도(`evals/benchmarks/decision_handoff_runtime.py`, 넘으면 "no truncation permitted"로 거부)와 같은 측정이다 |
| 절단 T1 | 한도를 넘으면 시작 행 + 첫 5행동 + `log_omission` 1행 + 들어가는 최대 행동 꼬리. 꼬리가 0이어도 안 들어가면 앞 5를 줄인다. 두 엔진이 같은 바이트를 받는다. **적용 0건**(최대 59,816자) |
| ID | `state_id = "x1-" + sha256("cuavb"␟split␟task_id)[:16]`. 원 task ID는 상태 밖 메타데이터(`source_task_id`)에만 둔다 |
| 클러스터 | om2w는 웹사이트(`task_id`의 `--` 앞, 63개), internal은 ID 끝 `(_data)?(_숫자)+`를 뗀 과제군(70개). 합 **133** |

Jev 1.13.0의 컨텍스트 한도는 GEODE 코드와 문서에 수치가 없다. `core/llm/model_pricing.toml`의 `[context_windows]`에 jev가 없고, `docs/eval/typesafe-decision-handoff.md`는 공급자의 한계 문서(jaggedness)만 링크한다. 그 페이지는 이번 네트워크 허용 범위 밖이라 열지 않았다. 그래서 GEODE 코드에 있는 같은 모양 상태의 한도(60,000자)를 썼다. 참고로 운영 경로(`core/agent/verify.py`)는 요청 4,000자, 후보 2,000자, 관측 16,000자로 훨씬 좁게 자른다.

## 3. 입력 계약(통합 담당 0022용)

`out/states.x1.jsonl`, 239행, `state_id` 오름차순.

| 필드 | 뜻 |
|---|---|
| `state_id` | `x1-` + 16 hex |
| `cluster_id` | `om2w:<웹사이트>` 또는 `int:<과제군>` |
| `split` | `"x1"` |
| `stratum`, `source_split` | 원 split(`internal` / `fara7b_om2w_browserbase`) |
| `language`, `headline` | `"en"`, `true` |
| `source_task_id` | 원 `task_id`(모델에 가지 않음) |
| `truncation` | `{applied, actions, chars_before, chars_after}`. 239행 모두 `applied=false` |
| `state` | `_VerificationState`의 네 키만: `task_contract`, `original_request`, `candidate_output`, `tool_observations` |
| `state_sha256` | `sha256(json.dumps(state, ensure_ascii=False, sort_keys=True, separators=(",",":")))`. `verdict_panel_runner.workloads_from_states`가 재계산해 대조한다 |

`state` 네 키의 매핑:

| 키 | 원천 | 변환 |
|---|---|---|
| `task_contract` | 없음(고정 문구) | 데이터셋과 무관한 웹 에이전트 완료 판정 계약. `build_cuavb.py`의 `TASK_CONTRACT`, sha256 `b7ddb4ccc3740637e87fd6503885e1866a7aa5272bf667d1a2088a875cc01d7c` |
| `original_request` | `instruction` | 그대로 |
| `candidate_output` | `final_answer` | 그대로. `<no_answer>` 4건도 그대로 둔다 |
| `tool_observations` | `web_surfer_log`(JSONL), `init_url`, `start_timestamp` | 아래 |

`tool_observations` 행:
- `t000`: `{"tool_call_id":"t000","tool":"session_start","input":{"init_url":<URL 또는 null>},"result":{"start_timestamp":<시각>}}`.
- `t001…`: 로그 한 줄마다 `{"tool_call_id","tool","input","result":null,"timestamp"[,"page_url"]}`.
  - `tool`: `arguments.action`(internal의 `computer_use` 포장은 벗긴다). om2w는 `action`과 같음을 확인했다.
  - `input`: `arguments`에서 `action` 키만 뺀 나머지 그대로. 에이전트의 `thoughts`, `fact`, `state_description`과 형식이 깨진 키도 원문대로 둔다.
  - `result`: 로그에 도구 결과가 없으므로 `null`.
  - `page_url`: 로그의 `url`이 비어 있지 않을 때만(internal). 행동을 낸 시점의 페이지 URL이다.
  - 로그의 `message`는 `arguments`와 번호로 완전히 재구성되므로 뺐다(6,180줄 전부 일치 확인). `type`·`source`는 상수라 뺐다.
- `t-omitted`(`log_omission`): T1 절단 때만. 이번에는 없다.

실행 쪽 계약(코드 확인, ext-src = integ-src b006154 사본):
- runner는 `json.dumps(state, ensure_ascii=False)`를 user 메시지 하나로 보낸다. `MatchedVerifierAdapter`가 `{state, questions}`를 만든다. 두 엔진이 같은 상태 바이트와 같은 Choice 질문을 받는다.
  - Choice 계약 digest: `question_sha256 e20e9318…0d63`, `llm_system_prompt_sha256 6955fc4c…dcc`, `llm_response_schema_sha256 8d4e52e8…dc8`(`length-stats.x1.json`에 전체 값).
- **Choice 단독이 필요하다.** 현재 `PanelUnit.validate`는 choice와 noul 출력을 둘 다 요구한다. X1은 (llm, choice)와 (jev, choice) 두 칸만 보낸다. 칸 순서는 4×4 Latin 회전의 2칸판(상태 순번 짝수 [A, B], 홀수 [B, A])을 제안한다.
- dispatch 순서: `out/workload-order.x1.json`. `verdict_panel.ordered_workload_ids(state_ids, split-manifest sha256)`, 즉 `sha256(state_id + 03002e70…)` 오름차순이다. 순서 목록 sha256은 `7a5c20529df70bd16482360499f0398b610e1f75f492b22fb08de455fcbd7695`이고, Run 담당의 재계산과 일치했다(run-log 23:58).
- 길이(`out/length-stats.x1.json`, tiktoken `o200k_base` 추정):

| 측정 | 최소 | 중앙 | p95 | 최대 | 합 |
|---|---|---|---|---|---|
| 상태 문자(E2E 측정) | 2,535 | 9,071 | 29,880 | 59,816 | 2,890,202 |
| Jev 본문 토큰 | 865 | 2,892 | 9,449 | 16,640 | 907,232 |
| Astra 입력 토큰(system + HTML escape된 입력) | 1,198 | 3,903 | 12,711 | 20,730 | 1,216,247 |

Astra 입력이 더 긴 것은 `html.escape`가 JSON 따옴표를 `&quot;`로 바꾸기 때문이다. 내용은 같다.

## 4. 채점 정의(통합 담당 0022용)

`out/gold.x1.jsonl`: `{state_id, source_split, source_task_id, annotators, votes{Correct, Incorrect}, majority_outcome, gold_accept, gold_rule}`. gold 수용 119, 거부 120(internal 90/64, om2w 29/56). 검토자 수: 1명 154, 2명 82, 3명 3.

엔진 출력은 패널 receipt의 `accepted`, `verdict`, `probabilities`(세 라벨), `q`를 쓴다.

| 이름 | 정의 |
|---|---|
| 결정 d | `accepted=true ∧ verdict="supported"` → 수용. `accepted=true ∧ verdict ∈ {contradicted, insufficient_evidence}` → 거부. `accepted=false` → 무효 |
| 정답 | d ≠ 무효 ∧ (d = 수용) = `gold_accept`. 무효는 오답(05 §3.2) |
| 이진 정확도(1차 재료) | 정답 수 / 239. `x1_binary_verdict_accuracy_delta` = (Jev 정답 − Astra 정답) / 239 |
| 오수용률 | #(d = 수용 ∧ ¬gold) / 120. 무효는 수용이 아니다 |
| 오거부률 | #(d ≠ 수용 ∧ gold) / 119. 무효는 수용하지 않은 것으로 센다 |
| TPR, TNR, balanced accuracy | TPR = #(수용 ∧ gold)/119, TNR = #(거부 ∧ ¬gold)/120(무효는 오답), BA = (TPR + TNR)/2 |
| p_accept | `probabilities["supported"]`(유효 출력만) |
| 수용 확률 AUROC | p_accept로 `gold_accept`를 가르는 Mann–Whitney AUROC, 동률 0.5. 한 클래스가 비면 not-measurable |
| 수용 확률 보정 | Brier = mean (p_accept − 1[gold])², ECE = p_accept 등폭 10구간 Σ (n_b/N_valid)·\|gold 비율 − 평균 p_accept\| |
| 선택적 위험(동결 τ) | q = receipt `q`(세 라벨 최댓값, M7과 같은 정의). 포함 = 유효 ∧ q ≥ τ. coverage = 포함/239, risk = 포함 중 오답/포함. τ는 `selection-freeze.json` 값 그대로. τ가 없으면 not-measurable |
| 오프라인 cascade(동결 τ) | 포함이면 Jev 결정, 아니면 Astra 결정(Astra 무효는 오답). 이진 정확도와 coverage |
| 쌍대 비교 | McNemar 정확 검정. b = #(Jev 정답 ∧ Astra 오답), c = #(Jev 오답 ∧ Astra 정답), p = min(1, 2·Σ_{i≤min(b,c)} C(b+c, i)/2^{b+c}). b + c = 0이면 p = 1 |

- **τ의 q를 바꾸지 않는다.** τ는 세 라벨 q로 적합됐다. 이진 투영의 q(max(p_accept, 1 − p_accept))로 선택적 위험을 계산하면 τ의 뜻이 바뀐다. 기존 `ChoiceRecord`에 이진 라벨을 넣어 재사용한다면, 선택적 위험과 cascade에는 receipt의 `q`를 따로 넘겨야 한다.
- 세 라벨 분포(gold 수용·거부별 supported / contradicted / insufficient_evidence 수)는 서술용으로 함께 낸다. gold는 contradicted와 insufficient_evidence를 구분하지 않는다.
- 참고값(결정에 쓰지 않음): `out/reference.x1.jsonl`. `uv_outcome_success`(Universal Verifier)·레거시 `mm_is_success`·`verifier_is_success`·`gpt_eval_score`(−1은 평가 없음)와 gold의 일치율. 데이터셋의 사람 집계 `majority_human_outcome_vote`는 우리 다수결과 비동률 239건에서 모두 같다. 동률은 이 필드에서 0(Incorrect)으로 처리돼 있다. `final_human_outcome_label`은 om2w 13건에서 다르다(심판 조정).
- 층: source split, 검토자 수(1 vs 2–3), `<no_answer>` 4건, 상태 길이 사분위. 클러스터 부트스트랩은 `cluster_id` 133개로 한다.

## 5. 누설 검사(자체, 빌드마다 실행)

`build_cuavb.py`가 states 파일의 정확한 바이트로 검사하고, 실패하면 파일을 쓰지 않는다. 결과는 `split-manifest.x1.json`의 `leak_check`에 있다.
- 상태 키가 정확히 네 개다.
- 라벨·검증기 필드 이름 23개(`human_judgement_outcome`, `uv_outcome_success`, `uv_rubric_score`, `gpt_eval_json`, `majority_human_outcome_vote`, `gold_accept`, `annotator` 등)가 states 파일에 0회 나온다.
- 사람 코멘트와 GPT 판정문(30자 이상 938개)이 states에 0회 나온다.
- 원 task ID가 상태 안에 0회 나온다.
- 참고: 맨 단어 `Correct`는 에이전트 문장에 1회 있다. `Incorrect`는 0회다.

## 6. 파일

| 파일 | 크기(B) | sha256 | 공개 등급 |
|---|---|---|---|
| `out/states.x1.jsonl` | 2,914,552 | `fa5b02661188ce988f4ca3586d7b0d17b894a944c577878a6bae77966b7cecab` | public 후보(MIT, §7) |
| `out/gold.x1.jsonl` | 77,715 | `44b57959e5ba0cfd986a09146026f29e23ec299dfac2743e0960c24da1512c65` | public 후보. Run은 attempt 끝까지 열지 않음 |
| `out/excluded.x1.jsonl` | 3,731 | `7d56df660e4912f2ba76d235209ab0fe7413a9e2059d3212105c1fceb043e2dd` | public |
| `out/reference.x1.jsonl` | 107,498 | `c44c811136dde5ae99fcdc73b75f0db29a8c901300f402da0b4cbb96c051e146` | public 후보(참고 전용) |
| `out/split-manifest.x1.json` | 3,726 | `03002e708f7e8148ef040da96e9979bd480bfa155244f75ac369387259c26f40` | public |
| `out/workload-order.x1.json` | 6,784 | `e631dac44e028224e41d39b6abbdafb078d468c87064f2f09948d12e0f3d3ba3` | public |
| `out/length-stats.x1.json` | 2,851 | `ebdd08949c3e30332489ba7d3359e22beb6c1b84c28af6b9031457ea100525cf` | public |
| `tools/fetch_cuavb.py` | 8,738 | `edf743f2a8fe43a49485b05d57a70cb6a91b4f2a1f2e41d6d7d3164cd593d9d8` | public |
| `tools/build_cuavb.py` | 18,960 | `7d2ed7ebbd34e6ebe53aa1f76486caf2be7c1abe241558f8303d754de6c9fd98` | public |
| `tools/verify_x1.py` | 6,356 | `b9786b6a82215a1f0b3897d599391c06b98417ba3129adad1e1bece5669b4104` | public |

원시 캐시(`<scratch>/ext-cache/cuavb/`, reproducible-cache): `raw/trajectories.text.jsonl` 5,392,256 B(`adc70a07…`), `raw/trajectories.labels.jsonl` 1,726,443 B(`1ffe3404…`), `raw/annotations.jsonl` 269,958 B(`01a7d3f7…`), annotations parquet 2개, 카드, `fetch-receipt.json`. 빌더가 raw sha256 세 개를 대조한 뒤에만 실행된다.

## 7. 공개 등급

- 라이선스는 MIT다. 사본에 저작권·허가 고지를 함께 두면 파생 파일 재배포가 허용된다. 카드에는 별도 저작권 줄이 없으므로 "Microsoft Research AI Frontiers, CUAVerifierBench(MIT)"와 논문 인용을 붙인다.
- 05 §11.8은 "라이선스 확인 전까지 withheld-private"다. 확인 결과 MIT이므로 states·gold·reference는 **public 후보**다. 실제 게시는 기존 공개 게이트(비밀 스캔, 신원 검토, 내용 주소 manifest)를 통과한 뒤에 한다. 로그에 외부 사이트 URL과 에이전트가 입력한 문자열이 있으므로 비밀 스캔은 생략하지 않는다.
- 원시 캐시와 parquet은 reproducible-cache다. revision·경로·sha256만 기록한다.
- 사람 라벨 원문(코멘트)은 재배포하지 않는다. gold에는 표 수와 다수결만 있다.

## 8. 한계

- **텍스트 변환본에서의 판정이다.** 사람 검토자는 스크린샷을 봤고 두 엔진은 보지 못한다. 로그에는 페이지 내용이나 도구 결과가 없고 에이전트의 행동·생각·메모만 있다. 판정 기준이 "관측으로 뒷받침되는 주장"을 요구하므로 `insufficient_evidence`가 많이 나올 수 있다(오거부 상승). 두 엔진이 같은 텍스트를 받으므로 쌍대 비교는 공정하지만, 사람 대비 절대 수준은 낮게 나올 수 있다. 문턱이 없는 수용 확률 AUROC를 함께 본다.
- 에이전트가 Fara-7B 하나다. om2w는 Online-Mind2Web 과제의 편향과 시간 유효성을 물려받는다. internal은 Microsoft 내부 과제라 원문 과제 정의를 확인할 수 없다.
- internal 154건은 검토자 1명이다. om2w의 동률 21건을 빼면 가장 애매한 사례가 빠져 과제가 쉬워진다.
- 60,000자 한도는 공급자가 밝힌 Jev 컨텍스트 한도가 아니다. 가장 긴 상태는 Jev 토큰 16,640(o200k 추정)이다. X1 admission에 가장 긴 두 상태(`x1-580a8e039ac4aefb`, `x1-f2684c4eaf078047`)를 넣어 두 엔진이 받는지 먼저 확인하기를 권한다.
- 공개 데이터셋(2026-04 공개)이라 두 모델이 학습에서 봤는지는 unknown이다. 날짜가 걸린 과제는 실행 시각(`start_timestamp`)을 입력에 넣어 두었다.
- UV 일치는 참고값이다. informed 단계는 UV 판정을 본 뒤라 쓰지 않았다.

## 9. 재현

```sh
# 원시 캐시(네트워크: huggingface.co만). pyarrow가 필요하므로 GEODE uv 환경 파이썬을 쓴다.
EXT_CACHE=<scratch>/ext-cache <geode-venv>/bin/python tools/fetch_cuavb.py
# 변환(표준 라이브러리만, raw sha256 대조 후 실행)
EXT_CACHE=<scratch>/ext-cache python3 tools/build_cuavb.py
# 자체 검사: 재빌드 바이트 동일, _VerificationState 239, workloads 239, 순서·길이 통계
EXT_CACHE=<scratch>/ext-cache PYTHONPATH=<geode-src> <geode-venv>/bin/python tools/verify_x1.py
```

2026-09-27 재실행 결과: 5개 산출물이 바이트 단위로 같았고 `passed=true`였다.
