# E2E 데이터: 원실험과 복구 계보의 공개 투영

이 디렉터리는 Jev v3의 E 트랙과 I 트랙에서 보존한 **기존 15개 실행/준비 계보와 별도 E8 계보**를 공개용으로 정리한 자료다. 초기 실패와 중단, 호출 전 거부, 미시작 셀, 최종 복구를 구분한다. 공개 투영에서 native 점수·판정·시간·사용량을 바꾸거나 재시도를 하나의 성공률로 합치지 않았다. E8의 후보 수준 사후 분석은 별도 `analyses/`에 두며 원 결과를 대체하지 않는다. 공개를 위한 변환이 있었으므로 원시 실험 폴더 전체와 같은 바이트라고 주장하지 않는다. 이 자료는 E8 추가분을 포함해 [PR #46](https://github.com/mangowhoiscloud/geode-eval-artifacts/pull/46)의 병합 커밋 `3bcf4044`로 `main`에 반영되어 GitHub에서 누구나 열람할 수 있다.

기존 15계보의 [source map](evidence/e2e-source-map.json)은 5,378개 사본을 유지한다. 별도 [E8 source map](evidence/e2e-source-map-e8.json)에 760개 사본을 추가해, 두 map이 선택한 공개 사본은 총 6,138개다. E8 추가분은 7,271,896바이트이며 기존 map과 원본 계보를 덮어쓰지 않았다. 기존 map에는 내보내기 도구가 내용을 읽지 않은 제외 파일/디렉터리와 별칭 6,215개 항목의 분류를 함께 기록했다. E8 map의 제외 항목 853개는 별도 범위다. 디렉터리 내부를 열지 않은 비밀/봉인 영역은 디렉터리 단위로만 표시하므로, 6,215는 모든 비공개 파일의 개수라는 뜻이 아니다. 공개 트리에 추가한 `_checks` 영수증은 원실험 파일이 아닌 공개 준비 검증 자료다.

## 무엇을 포함했는가

| 공개 자료 | 기존 15계보 | E8 추가 | 역할 |
|---|---:|---:|---|
| 고정 spec, attempts, analysis, results, freeze, trial/verifier/runtime 요약 등 JSON/JSONL | 3,140 | 437 | 계획·관측·판정·계보의 원래 수치와 결정을 보존 |
| Native reward | 181 | 26 | 개별 trial verifier의 원래 `0` 또는 `1` |
| 실행기·가드·프로토콜의 검토된 사본 | 107 | 9 | 실행/분석 소비 경로를 조사하는 코드 근거 |
| 자체 작성 synthetic inbox payload | 216 | 32 | 실제 사용한 입력과 정답 계약; 계보별 중복 포함 |
| Harbor task-bundle | 1,734 | 256 | instruction, task.toml, 검증 코드, case, 의존성 해시 |

같은 payload와 검증 코드가 여러 계보에 반복되어도 각 계보의 원본 SHA를 유지했다. 숫자형 사용량과 `reasoning_tokens`는 측정치로 보존하지만, 모델의 비공개 추론 내용은 포함하지 않는다. 판정의 구조화된 확률·q·admission·오류 종류와 verifier의 구조화된 체크 결과는 포함한다. 연구자가 작성한 `analysis.decision.rationale`은 과학적 결론이므로 보존했다.

자체 작성 입력은 주문 상태 조회를 흉내 낸 synthetic inbox다. 코드의 생성 계약과 변환된 payload/task-bundle을 확인해 포함했으며, 별도 `DO-NOT-OPEN` 원천 폴더를 열거나 다시 추출하지 않았다. 원 `e2e-sources.json`에는 실행하지 않은 여분 원천의 식별자도 있어 제외했다. 이미 만들어진 소비 대상 task bytes와 원본 해시만으로 공개된 task를 확인할 수 있다. 외부 데이터셋의 본문을 이 디렉터리에 섞지 않았다.

## 계보를 먼저 선택한다

`jev-verdict-e2e-rN`은 E 계보, `jev-intent-harbor-rN`은 I 계보다. 접미사 번호와 소스 버전 번호는 같지 않다. 정확한 코드는 각 계보의 `source-pin.json` 및 해당 phase의 `freeze.json`에 있다. 접미사가 없는 두 디렉터리도 초기 준비/실패 기록으로 남아 있다.

| 계보 | 보존한 관측 또는 준비 상태 |
|---|---|
| E 초기 | U0d 2/4 관측, 2 invalid; primary not-measurable |
| E r1 | U0d 4/4 strict; U0e 1/2 strict, 유효한 의미적 실패 포함 |
| E r2 | U8c 6/36 관측, 5 valid strict + 1 invalid; primary not-measurable |
| E r3 | U0f 2/2 strict; U0d는 E r1 별칭 |
| E r4 | 준비 판본; 실제 phase 결과 없음 |
| E r5 | U0d 4/4, U0e 1/2, U0f 2/2, U8c 36/36 strict; U7r0 호출 전 중단 기록 |
| E r6 | U7r0 21/36 관측: 19 valid strict + 2 invalid, 15 미시작; primary not-measurable |
| E r7 | U0f 2/2; U7r0와 r1 각각 36/36 valid strict. 두 반복은 같은 12개 과제의 반복이며 72개 독립 과제가 아님 |
| E r8 — 별도 추가 map | U0e 2/2 valid strict; U8n 24/36 관측: 23 valid(12 strict + 11 semantic failure), 1 invalid, 12 미시작. 원 primary not-measurable; 별도 사후 완성 유효쌍 11개 |
| I 초기 | admission 준비/동결 기록; native 결과 없음 |
| I r1 | admission 2/2 strict |
| I r2 | natural 2/6 관측, 두 셀 invalid; admission/입력은 I r1 별칭 |
| I r3 | 준비 판본; 실제 phase 결과 없음 |
| I r4 | admission 2/2; natural 4/6 관측, 3 valid + 1 invalid, strict 0; primary not-measurable |
| I r5 | admission 2/2; natural 6/6 valid, strict 0/6; 원 verifier 계약 결함 계보 보존 |
| I r6 | admission 2/2; natural 6/6 valid strict; 소스 수정 후 별도 계보 |

위 표의 셀 수는 `results.json`의 planned/observed 및 arm별 strict count를 설명한 것이다. `primary.numerator`는 단위에 따라 성공 개수가 아니라 **두 arm의 차이**다. 예를 들어 I r5와 I r6 모두 natural primary는 Δ 0/3이지만, 앞쪽은 양 arm 모두 0/3, 뒤쪽은 양 arm 모두 3/3이다. U7도 Δ 0/12와 각 arm의 12/12를 함께 읽어야 한다. `mixed`는 통계적 동등성이나 실무적 대체 가능성의 입증을 뜻하지 않는다.

E r7의 코드 소스는 source 5, I r6의 코드는 source 7이다. E r6의 전송 오류를 E r7로 덮지 않았고, I r5의 실패와 I r6의 성공을 한 표본으로 합치지 않았다. **위 15개 기존 계보의 U8n**은 선행 admission 조건을 충족하지 못해 미실행 종결되었으며, 이 자료에 새 성공·실패 행을 만들어 넣지 않았다. 별도 source 7 / E8은 admission 통과 후 U8n 실행이 중단된 종료 계보다. E8 원 자료와 추가 map은 공개 패키지에 들어 있으며, 기존 15계보와 별개로 보존한다. 새 U8n live 시행은 계획하지 않는다. 전체 단위 상태와 개정 근거는 이 보고서의 등록/결과 문서를 함께 읽어야 한다.

## E8 부분 관측: 후보 정답과 전달 성공을 구분한다

[E8 사후 분석](analyses/u8n-observed-pairs-20260928/README.md)은 양쪽 arm이 유효하게 종료된 11쌍·22시행만 기술한다. 원천은 4개이며 조건별 분모는 c1m0=4, c0m1=4, c1m1=3이다. 양군 root·수리는 Astra이고 판정기만 A=Astra, B=Jev Noul이다. A의 strict/recovered는 11/11, B는 0/11이지만, **B의 마지막 후보는 기존 task oracle를 11/11 통과했다.** 후보 gold=(모순 없음, 근거 부족 없음)과 달리 Jev가 근거 부족을 계속 표시해 모든 전달을 보류했다. 최종 `final_text`가 빈 B의 native task oracle 통과 0/11과 후보 진단 11/11은 서로 다른 값이다.

원 U8n 계획 36셀·18쌍·6원천과 primary의 null 분자/분모는 변경하지 않았다. 무효 B 1개와 같은 짝의 유효 성공 A 1개를 함께 제외했으며, 미시작 12개의 결과는 알 수 없다. `attempts.jsonl` 25행은 실제 시행 24개와 분석용 aggregate sentinel 1개다. 사후 분석은 중단·순서에 영향을 받은 부분 표본이므로 신뢰구간·비열등성·일반화 결론을 붙이지 않는다. 양군 false completion 0/11도 B의 최종 승인이 0건이라는 사실과 함께 읽는다.

## 결과를 읽는 순서

1. 해당 phase의 `run-spec.json`에서 질문, 모델·effort, 반복, 입력 순서, 고정 분모, 무효화 조건을 읽는다.
2. `freeze.json`, `source-pin.json`, `e2e-slots.jsonl`로 소스·task·실행 셀을 연결한다. 원래 계획에 있었으나 시작하지 않은 셀도 여기 남는다.
3. `execution-receipt.json`이 있는 경우 실제 종료 코드를 확인한다. 초기 계보 중 이 영수증이 원래 없는 경우에는 새 영수증을 발명하지 않았다.
4. `attempts.jsonl`의 identity/parent/sequence, validity/outcome, selected flag와 `results.json`의 전체 분모를 대조한다. aggregate 행은 새로운 모델 시행이 아니다.
5. 개별 `trials/*/trial-receipt.json`, `result.json`, `verifier/verifier-receipt.json`, `verifier/reward.txt`를 읽는다. agent/runtime 요약과 구조화된 `verification.json`은 원인과 호출 회계의 보조 근거다.
6. `analysis.json`의 원래 metric/decision을 읽는다. E r7 U7r1의 신뢰도 지표도 이 native 분석에 포함되며 별도 재분석은 하지 않았다.

E r7 U7r1은 36셀의 유효성과 성공 판정이 유지되지만, 시작 시각 차이로 2슬롯이 paired-latency에서 제외되어 시간 비교는 10/12슬롯이다. E r7의 C arm은 24셀 모두 Jev 판정을 수락하고 Astra fallback은 0회였다. 이는 오류를 fallback이 얼마나 구제하는지를 이 표본으로 관측하지 못했다는 한계다. 540초 예산의 성공을 예산 증가의 인과 효과나 최적 시간으로 해석하지 않는다.

## 변환과 원본 해시의 경계

[기존 source map](evidence/e2e-source-map.json)과 [추가 E8 source map](evidence/e2e-source-map-e8.json)은 파일마다 다음을 기록한다.

- `source_path`: 공개 기준의 상대 경로. 디렉터리 별칭은 `alias_of`로 기록하고 사본 trial을 중복 생성하지 않았다.
- `source_sha256` / `source_bytes`: 읽고 공개 투영한 **원본 바이트**의 해시와 크기.
- `public_path` / `public_sha256` / `public_bytes`: 이 저장소에 실린 **변환된 바이트**의 해시와 크기.
- `changed_fields`: 누락한 본문 필드, 경로/계정 식별자 치환 위치. 제거한 값은 본문 대신 해시로만 연결한다.
- 제외 항목의 `content_read=false`: 해당 내보내기 실행에서 내용을 열지 않았으므로 원본 SHA는 `null`이다. 이 필드는 exporter의 동작 범위이며, 별도의 공개 provenance 메타데이터 검토까지 하지 않았다는 뜻은 아니다. 파일 경로나 크기의 존재 관측을 원문 검증으로 과장하지 않는다.

JSON은 키 정렬과 들여쓰기를 표준화했다. 과제·분모·metric 값·판정·목록 순서와 길이는 유지했다. 계정 식별자는 일관된 익명 토큰으로, 호스트 경로는 `source-runs/...` 또는 불투명한 경로 토큰으로 바꿨다. `/tests`, `/logs` 등 검토한 컨테이너 내부 경로는 재현 코드의 계약으로 남아 있으며 개인 호스트 경로가 아니다.

**중요: JSON 안의 `run_spec_sha256`, `attempts_sha256`, evidence SHA, frozen file SHA는 원본 증거를 가리킨다.** 공개 사본의 SHA인 것처럼 바꾸지 않았다. 따라서 공개 사본만 원래 freeze/native validator에 넣어 바이트 동일성 검사를 통과한다고 주장하지 않는다. 공개 바이트의 무결성은 source map의 `public_sha256`로 확인한다. 비공개 원본을 가진 연구자는 `source_sha256`로 원래 권위까지 검증할 수 있다.

## 포함하지 않은 것

위 `evidence/e2e/` native 투영에서는 원시 transcript/ATIF/cast, 모델 요청·응답 본문, provider의 비공개 추론, 세션 DB/WAL, runtime home, 환경 자격증명, 개인 계정 정보, 영상·이미지, 중복된 `artifacts/logs` 사본을 제외했다. 기본 로그 파일의 자유 형식 본문도 공개하지 않았다. 정해진 오류 종류·시간·유효성·사용량 결손은 native 요약에 남으므로 실패가 사라지는 것은 아니다. 공개 자료는 완전한 대화 재생 자료나 모든 provider 요청을 재조립할 수 있는 덤프가 아니다.

별도 [사후 분석 보완본](analyses/u8n-observed-pairs-20260928/README.md)은 승인된 합성 입력·가시 후보 범위에서, 완성 유효 22시행의 마지막 판단 state만 추가로 공개한다. 작성된 task contract, 이미 공개된 synthetic request, 마지막 가시 `candidate_output`, 실제 lookup 관측을 포함해 기존 oracle로 후보 정답을 다시 검사할 수 있다. 주변 시스템 문맥·provider reasoning·앞선 전체 대화는 포함하지 않으며, 기존 E8 source map을 덮지 않고 별도 공개 state map으로 연결한다.

과거 receipt에 실제 관측된 human review 여부를 바꾸지 않았다. 위임된 에이전트의 플레이어 조작을 사람 시청으로 승격하지 않는다. 비용의 `actual_charge_usd` 및 `reported_cost_usd`가 미상인 경우 그대로 `null`이며, 관측된 토큰 기반 추정액과 실제 청구액은 별개다. `observed_sum=0`과 `total=null`을 무료라는 뜻으로 읽으면 안 된다.

## 검증 및 재구성

[공개 보존 검사](evidence/e2e/_checks/preservation-check.json)는 모든 공개 파일의 원본/사본 해시 대응, native 결과의 분모·primary·pairing, 분석 metric/decision/선택 ID, attempts의 계보·유효성·선택을 대조한다. [개인정보 패턴 검사](evidence/e2e/_checks/privacy-scan.json)는 기존 GEODE Harbor publication scanner로 수행했다. 패턴 검사는 파일 유형/필드 경계 검토를 보완하며, 전세계 모든 개인정보 탐지의 보장은 아니다.

원본 campaign이 있는 환경에서 아래 명령은 공개 파일 분류를 먼저 확인하고 새 디렉터리에 재생성한다. 기존 결과를 덮어쓰지 않으며 모델·Docker·네트워크를 호출하지 않는다.

```sh
python tools/export_e2e.py --input retained-campaign --output fresh-public-report --plan
python tools/export_e2e.py --input retained-campaign --output fresh-public-report
```

기존 15개 계보를 만든 [원 내보내기 도구](tools/export_e2e.py)의 SHA-256은 `cbe0374e540f23397199f1e7f8a49202dacd3984b55c7a6c7213827bc92420ef`다. 원 source map의 `generator` 경로와 `generator_sha256`은 이 파일의 실제 바이트와 일치한다. 별도 [계보 선택 도구](tools/export_e2e_subset.py)에 `--roots`를 추가해 정확한 계보를 선택할 수 있으며, 잘못된 이름·없는 폴더·심볼릭 링크·기존 출력 덮어쓰기를 거부한다. 새 map은 이 선택 도구의 실제 파일명과 해시를 기록한다.

E8 추가분은 아래 계보 선택 절차로 별도 staging에 내보낸 뒤, 종료된 원 결과를 보존해 병합 전 준비본에 추가했다. 같은 절차를 재현할 때도 기존 공개 폴더가 아닌 **새 staging 디렉터리**를 사용한다. 실행이 종료됐다는 사실은 36셀 전체가 완료됐다는 뜻이 아니다.

```sh
python tools/export_e2e_subset.py --input retained-campaign --output fresh-e8-staging --roots jev-verdict-e2e-r8 --plan
python tools/export_e2e_subset.py --input retained-campaign --output fresh-e8-staging --roots jev-verdict-e2e-r8
```

현재 E8의 760개 사본은 `evidence/e2e/jev-verdict-e2e-r8/`에 있고 대응 해시는 별도 `evidence/e2e-source-map-e8.json`에 있다. 기존 15개 공개본과 원 `e2e-source-map.json`은 덮어쓰지 않았다. 익명 account 토큰은 각 map 안에서만 일관되므로 서로 다른 map의 같은 토큰을 같은 계정으로 결합하면 안 된다. 기존 8,655파일 패킷의 모델 없는 검증·지원 결과 재계산은 성공했으나, 이 결과를 E8 추가분까지 넓히지 않는다.

공개 자료로 과제 조건을 재구성하려면 원하는 계보의 `source-pin.json`에 기록된 GEODE commit을 별도로 체크아웃하고, `payloads/`와 `task-bundle/`의 입력·검증 코드·의존성 해시를 사용한다. 별칭은 source map의 원래 대상 계보에서 해소한다. 실행기 사본의 개인 경로/계정 토큰은 현 환경에서 별도 설정해야 하므로 그대로 실행 가능한 호스트 구성이라고 주장하지 않는다. 원시 대화·자격증명·사용하지 않은 봉인 원천과 옛 호스트 디렉터리는 재구성하지 않는다. 새 실제 호출은 새로운 실행이며 이 실험의 원래 관측을 재생산한다고 보장하지 않는다.
