# U8n 완결 유효 11쌍의 사후 후보 재채점

이 보완본은 E8의 전체 36셀 primary를 대체하지 않는다. E8은 24셀 관측(23 valid, 1 invalid) 후 중단됐고 12셀은 미시작이다. 전체 primary의 numerator/denominator는 null, 값은 `not-measurable`이다. 여기서는 **양쪽이 모두 valid인 11쌍**만 사후 분석한다. 4원천이고 조건별 분모는 c0m1 4, c1m0 4, c1m1 3이다. CI·NI나 새로운 우월성·승격 판단을 추가하지 않았다.

| 공개 자료에서 재계산한 범위 | A | B |
|---|---:|---:|
| 마지막 실제 후보 gold c0m0 · 모든 항목 correct | 11/11 | 11/11 |
| native strict 성공 | 11/11 | 0/11 |
| native recovered | 11/11 | 0/11 |
| 최종 전달 보류 | 0/11 | 11/11 |

B의 마지막 Jev 판단은 11개 모두 `missing_evidence=true`이고 `external_verification_required`로 종료됐다. 후보가 과제의 정답 조건을 충족했다는 것과 실제로 최종 응답을 전달했다는 것은 다르다. 원천별 inbox 항목 수는 8/9/12개이며 각 payload의 실제 항목 수로 검사했다.

## 공개한 내용과 경계

기존 [E8 공개 결과](../../evidence/e2e/jev-verdict-e2e-r8/u8n/results.json)와 [원 공개 매핑](../../evidence/e2e-source-map-e8.json)은 그대로다. 기존 exporter에서 제외한 `verification.inputs`를 전부 복원하지 않았다. 사용자가 별도로 승인한 합성실험 입력·가시 후보 범위에서, 22개 선정 시행의 **마지막 판단에 대응하는 state 하나씩**만 [final-verification-states.jsonl](final-verification-states.jsonl)에 담았다.

- `task_contract`: 코드의 작성된 inbox 계약과 정확히 같다. 주변 시스템 프롬프트가 아니다.
- `original_request`: 이미 공개한 합성 payload items로 만든 요청과 정확히 같다.
- `candidate_output`: 마지막 가시 후보이며 기존 inbox 답변 스키마를 통과한다. 모델의 비공개 추론은 포함하지 않는다.
- `tool_observations`: 실제 `lookup_order_status` 관측만 포함한다. JSON 문자열 input에는 합성 id/order_id만 있고, 구조화된 result는 공개 orders와 대조된다.

입력 items/orders는 기존 공개 payload를 경로와 SHA로 재사용한다. 인증정보·계정지문·환경설정·주변 시스템 메모리·provider reasoning·앞선 모든 state·외부 데이터셋 본문은 추가하지 않았다. 기존 identity/path 투영 규칙을 승인된 필드에 적용했으며 변환이 필요한 값은 0개였다. 예상하지 못한 state 필드·비밀·개인 경로는 내보내기 차단 조건이다.

[public-state-map.json](public-state-map.json)은 native 원파일 SHA, 선택한 입력/판단 pointer, state SHA, 공개 JSONL 행 SHA를 구분한다. Native 파일 SHA는 원본 참조이며 공개 파일 SHA가 아니다. 재현은 공개 payload와 이 제한된 state로 `noul.score_trial`을 호출하며, 후보 gold를 저장된 label로 대체하지 않는다. 계산한 gold를 기존 공개 trial receipt의 마지막 파생 판정과 대조한다.

## 재현

Python 3.12 환경과 GEODE의 기존 의존성을 사용한다. GEODE checkout은 `802cfd4b9d3220ce2be1744e8cf22161345b0954`이며 해당 채점 owner는 source7에서 사용한 바이트와 같다. [실행기](recompute_posthoc.py)는 map에 고정된 owner SHA를 확인한다. 의존성 설치나 새 모델 호출은 수행하지 않는다.

저장소 루트에서, 아래 경로를 자신의 checkout에 맞춰 지정한다. 출력 경로는 아직 존재하지 않아야 한다.

```bash
PYTHONDONTWRITEBYTECODE=1 python -B \
  reports/e2e-validation/jev-v3-20260927/analyses/u8n-observed-pairs-20260928/recompute_posthoc.py \
  --report reports/e2e-validation/jev-v3-20260927 \
  --source /path/to/geode-checkout \
  --output /path/to/new-public-posthoc-result.json
```

실행기는 공개 파일과 제한된 state만 읽으며 native run 폴더에 접근하지 않는다. 원본 E8 map·payload·trial receipt·state 행·채점 owner의 SHA가 다르면 거부한다. 네트워크와 자식 프로세스 호출도 차단한다. 실제 오프라인 실행 exit 0 결과는 [recomputed-results.json](recomputed-results.json)이다. 이 파일은 사후 재계산 결과이며 기존 native 분석을 덮지 않는다.

새 보완본의 제작 과정에서는 승인된 22개 native verification 파일에서 명시한 필드만 추출했다. **독자 재현 단계**는 그 native 파일을 요구하지 않는다. 공개용 필드 매핑과 스크립트는 준비된 바이트이며, 저장소 게시 여부는 상위 publication manifest가 결정한다.
