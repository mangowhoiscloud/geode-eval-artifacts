# Recovered execution observability

## 한국어

이 자료는 종료된 Terminal-Bench 2.1 실행에서 보존된 숫자 필드를 복구한 분석용 projection입니다. 재실행이나 점수 보정이 아닙니다. 기존 run spec, attempt ledger, selected reward와 제외 규칙은 그대로 유지합니다.

| 복구 항목 | GEODE | Codex |
|---|---:|---:|
| 호출별 usage가 검증된 trial | 401 | 418 |
| usage event | 4,709 | 12,214 |
| cache 값이 누락된 event | 648 | 0 |
| 구조화된 완료 명령 exit code | 4,344 | 7,085 |
| 그중 nonzero exit | 569 | 719 |

GEODE는 해당 trial의 session ID로 월별 usage record를 연결하고, Codex는 보존된 session JSONL의 누적 usage와 호출별 usage를 교차 검증했습니다. 두 경로 모두 합계가 Harbor result와 일치하는 경우만 `verified-call-usage`로 표시합니다. Codex의 중복 누적 snapshot 25건은 중복 계상하지 않습니다. 공개 event에는 숫자, 시각, 원본 record 해시만 남깁니다.

`input_tokens`에는 cached input이 포함됩니다. cache 값이 일부 누락된 trial은 `cached_input_tokens: null`이며, `observed_cached_tokens`는 확인된 부분합입니다. GEODE export의 cache 필드명 불일치 때문에 기존 ATIF의 0은 cache 미사용의 근거가 아닙니다. 호출별 usage와 ATIF tool step의 대응은 확정하지 않았으므로 replay 진행 위치와 usage event를 동기화하지 않습니다.

단계별 시간은 Harbor result의 UTC 시작·종료 시각 차이입니다. GEODE 435개 trial의 네 단계와 Codex 435개 trial의 environment/agent setup, 430개 trial의 execution/verifier를 복구했습니다. setup에서 중단된 경우 이후 단계는 `not-reached`이며 0초가 아닙니다. 단계 합계에는 teardown과 단계 사이의 간격이 포함되지 않아 trial wall과 다를 수 있습니다.

명령 exit code는 실행이 완료된 shell command의 결과입니다. 실패를 기대하는 검사나 탐색도 nonzero를 반환할 수 있으므로 agent tool 오류율 또는 benchmark 실패율로 해석하지 않습니다. CPU 사용률, peak RAM, 실제 청구액은 복구하지 않았습니다. `reported_estimate_usd`는 producer가 남긴 추정치일 뿐 subscription 청구액이 아닙니다.

## English

This is a numeric analysis projection recovered from preserved evidence, not a rerun or a score correction. Frozen attempts, selected rewards, exclusions and score authority are unchanged. GEODE monthly usage is joined through the private trial session identity; Codex cumulative and last-call usage are reconciled using the existing v13 parser. Verified call totals match the Harbor result. Private session identities, prompts, outputs and provider reasoning are not published.

Missing cache fields remain null. Observed cache is a subtotal when any event is missing, and cached input is already included in input tokens. Usage events are not mapped to ATIF tool steps. Phase durations come from UTC timestamp differences, not CPU measurements; unentered phases are not zero. Completed command exit codes are not tool invocation errors. Reported cost estimates are not subscription billing. The primary full-suite metric remains ineligible; the existing 429 common-cell secondary comparison is unchanged.

## Files and reproduction

- `data/observability.json`: 890-cell presentation projection, including 20 not-run cells.
- `data/private-source-inventory.json`: hashes and sizes of withheld monthly sources; no private paths.
- `data/source-hashes.json`: source digests, with native session paths withheld.
- `data/recovery-check.json`: numeric coverage and original-evidence integrity checks.
- `recover-observability.py`: deterministic producer; requires the preserved private run and monthly usage records and a new output directory.
- `verify-observability.py`: independent numeric, source-hash and privacy check; requires the private full hash map.

`data/source-hashes.private.json` and the original session/monthly files remain private. Public hashes support provenance but do not make withheld bytes publicly reproducible. UTC is canonical; the presentation displays KST. The parent run's `analysis-observability-v20.json` uses the existing `geode.eval-analysis@1` contract.
