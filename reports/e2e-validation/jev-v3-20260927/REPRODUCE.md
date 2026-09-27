# Recalculate a result, inspect a replay, or run a new experiment

이 패킷에서는 **공개된 관측값으로 결과를 다시 계산하는 일**, **기록된 실행을 열람하는 일**, **모델을 새로 호출하는 일**을 구분합니다. 아래 기본 명령은 첫 번째 작업만 수행합니다. 파일의 해시를 확인하는 데서 멈추지 않고, 기존 GEODE 분석 함수를 호출해 점수와 2,000회 source-cluster bootstrap을 다시 계산합니다.

The default recipe is a **model-free numerical reconstruction from public observations**. It does not rerun the original provider requests, certify the private execution environment, or create new experimental evidence. Original native results and the separately named post-hoc corrections remain separate.

| Reader task | Public starting point | What can be checked | Boundary |
|---|---|---|---|
| Recalculate U2 Choice and Noul | Selected attempts and typed receipts, published test states/gold/aliases, selection freeze | 216 headline states and 24 outside-scope states; paired scores, calibration auxiliaries, raw ranking, cascade simulation and cluster intervals | Raw response strings and private closure evidence are withheld; response parsing and original execution validity are not reproduced |
| Recalculate original U4 | Published forward/reverse pointwise score rows, candidate pools, grades and aliases | Original winners, 80 pool outcomes, summary, source-cluster CI and original conclusion | Retains the original invalid-order flags; does not silently apply the parser correction |
| Recalculate corrected U4/X2 | 1,280 exact numeric pointwise answer strings, original dispatch observations and approved outcome grades | Raw parsing, all 320 pool selections/outcomes, summary, split statistics, the fixed cluster-bootstrap intervals and original decision rule | The 640 Astra listwise orders retain observed winners; their raw responses are unavailable. No external task/candidate text or provider reasoning is included |
| Inspect a recorded E2E run | [E2E data guide](E2E-DATA.md) and the linked recording/trajectory evidence | Observed actions, feedback, delivery and recorded terminal outcome | Playback is not a new model run and is not an independent task verifier |
| Recalculate U8n final-candidate diagnoses | [E8 post-hoc inputs and command](analyses/u8n-observed-pairs-20260928/README.md) | Existing rule-based scoring of 22 disclosed final states, exact eligible-pair membership and retained delivery outcomes | Four source tasks and 11 complete valid pairs selected after interruption; original full-run primary stays null, with no CI or NI claim |
| Run a new live experiment | Pinned GEODE source, original study methods and task contracts | A separately frozen new observation | Requires credentials, provider access, current quotas/budget, appropriate task data and runtime infrastructure; inference and timing are not deterministic |

## 1. Prepare source and dependencies once

Use Python 3.12 or newer. The source checkout is pinned to commit `802cfd4b9d3220ce2be1744e8cf22161345b0954`; the helper rejects another HEAD or modified metric/selection/panel/parser/candidate owner files. The original U2/U4 measurement revisions remain recorded in their own specifications. The pinned current owner is used here to reconstruct their retained numerical observations, not to relabel their source history.

These setup commands need network access to obtain the repositories and dependencies. They make no model calls. Run them from a directory where the two new checkout names do not already exist:

```sh
git clone https://github.com/mangowhoiscloud/geode.git geode-source
git -C geode-source checkout --detach 802cfd4b9d3220ce2be1744e8cf22161345b0954
git clone https://github.com/mangowhoiscloud/geode-eval-artifacts.git geode-eval-artifacts
uv sync --project geode-source --frozen --no-dev
```

Use the artifact repository commit linked by the release you are reviewing. A local prepared package and a remotely published commit are different states. Record `git -C geode-eval-artifacts rev-parse HEAD` in your own review receipt; the calculation output also lists every consumed public file's SHA-256. If source and dependencies are already installed, the following calculation itself runs offline and needs no API key, subscription login or Docker daemon.

## 2. Recompute and assert against the published results

From the same parent directory:

```sh
GEODE_SOURCE="$PWD/geode-source"
JEV_PACKET="$PWD/geode-eval-artifacts/reports/e2e-validation/jev-v3-20260927"
PYTHONDONTWRITEBYTECODE=1 "$GEODE_SOURCE/.venv/bin/python" -B \
  "$JEV_PACKET/tools/recompute_results.py" \
  --source "$GEODE_SOURCE" --mode all > recomputed-results.json
```

The helper reads the existing source/public maps and the additive [numeric response disclosure receipt](corrections/numeric-parser-20260928/numeric-response-disclosure.json), and verifies the public hashes before consuming data. A source SHA retained inside a redacted receipt is resolved through those maps; it is never compared directly with the redacted file's bytes. The maps are integrity indexes inside the reviewed artifact commit, not external signatures.

The calculation then calls these existing owners:

- U2: `decision_metrics.choice_record` and `condition_records`, followed by the original `study/drivers/jev-panel-r5/u2_analysis.py::reports`. Frozen temperatures and τ are reused. Neither is refit on test data.
- Original U4: `score_selection.load_pools`, `attach_grades`, and the original `score_main_analysis.py::summarize_score`. Candidate IDs and both score orders determine the selection again; the resulting outcomes must match the original 80 rows exactly.
- Corrected U4/X2: reparse all 640 Jev pointwise strings with `typesafe.parse_systemone_answers` and validate all 640 Astra pointwise numeric strings using the existing `remeasure.py` contract. Rebuild both presentation orders through native `select_by_score`, `_pointwise_outcome`, `_listwise_outcome` and `_acceptable_value`; original and corrected per-pool outcomes must match exactly. Then call `score_selection.summarize_outcomes` and the original `score_main_analysis.py::interval`, including the published split summaries and X2 split intervals. The original manifest digest determines the same seed, source grouping and 2,000 bootstrap resamples. The imported parser and candidate owner paths and bytes are checked against the pinned checkout.

An assertion mismatch or missing public dependency exits nonzero. Success prints `status: matched-published-numerical-results`, the recomputed metrics, native owner hashes and consumed public input hashes. It also explicitly reports `model_calls: 0` and `native_run_bundle_validation: false`. After the initial read-only Git identity checks, the helper rejects network connection/DNS and subprocess attempts. It creates no evidence files; the shell redirect above writes your separate review result.

Expected primary values are:

| Mode | Quantity | Expected numerator / denominator | Expected interval |
|---|---|---:|---|
| `u2` | Choice paired accuracy difference, headline | −2 / 216 | Exact interval and all other report fields are checked against the published Choice report |
| `u2` | Noul joint accuracy difference, headline | −90 / 216 | Exact interval and all other report fields are checked against the published Noul report |
| `u4-original` | Original controlled selection difference | −21 / 80 | Original source-cluster interval, before numeric parser correction |
| `score-corrected` | Corrected U4 difference | −20 / 80 | [−0.3522894385026738, −0.1625] |
| `score-corrected` | Corrected X2 difference | −30 / 240 | [−0.17216117216117216, −0.08044827586206903] |

Each mode can be run separately by replacing `--mode all`. Full U2 reconstruction includes many 2,000-replicate auxiliary intervals and takes longer than checking a file hash. The helper prints its JSON only after the selected modes finish.

The separately disclosed U8n final candidates use a smaller existing-owner recipe. From the same parent directory, run:

```sh
PYTHONDONTWRITEBYTECODE=1 "$GEODE_SOURCE/.venv/bin/python" -B \
  "$JEV_PACKET/analyses/u8n-observed-pairs-20260928/recompute_posthoc.py" \
  --report "$JEV_PACKET" --source "$GEODE_SOURCE" \
  --output u8n-posthoc-recomputed.json
```

The output path must not already exist. This recomputes candidate gold from the disclosed task contract, synthetic request, candidate and actual lookup observations using `noul_conditions.score_trial`; it also verifies the original/public mapping and derives all eligible pairs from the public trial receipts. Expected candidate correctness is 11/11 for each arm, while retained strict/recovered delivery is Astra 11/11 and Jev 0/11. It does not relabel intermediate correctness as delivered success or validate the undisclosed native execution environment. The main `--mode all` command covers the panel and numeric correction; this separate command covers the U8n post-hoc candidate diagnosis.

For a separate publication-integrity check, use the existing [panel exporter verification](PANEL-DATA.md#verify-and-reaggregate-offline). That check and this reconstruction serve different purposes; neither grants authority to modify the original observations.

## 3. State exactly what remains unreproduced

**Public projection boundary.** The original private analyzer entry points also validate original local paths, unchanged native digests, account/block receipts and unredacted responses. Those checks cannot honestly be run unchanged on this redacted package. The helper adapts only input lookup and the typed observation join, then invokes the native numerical owners. It does not bypass an execution gate to claim a valid new run.

**Parser correction boundary.** The [numeric correction packet](corrections/numeric-parser-20260928/README.md) now adds exactly 1,280 retained numeric parser-input strings in [numeric-responses.jsonl](corrections/numeric-parser-20260928/numeric-responses.jsonl). Every string is joined to its original dispatch file digest, one-based line, JSON pointer, raw-answer digest and question digest. The fixed rubric is the only natural-language content in these Jev answers; Astra answers contain numbers only. Jev `raw_answer` is the adapter serialization of the answers object, not a full HTTP/provider response. All 1,920 order cells remain in the matrix, including 640 listwise orders whose native observed winners are retained without raw-response replay. These additions reproduce the parser-to-outcome correction and statistics; they do not reproduce private provider reasoning, transport or live execution. The publication map now identifies the revised public README while retaining its original source SHA and previous public SHA; the additive disclosure receipt binds the prior/current map digests and the exact numeric addition.

**External input boundary.** X2 numeric answers, candidate IDs, retained grades and per-pool metadata suffice for the included parser-to-CI reconstruction. Rebuilding Mind2Web task/candidate inputs or making new calls requires independently acquiring the pinned upstream data and applying the documented transformation under the upstream terms. The package does not contain the full external task context or original archive. See [sources and disclosure](SOURCES-AND-DISCLOSURE.md).

**Live execution boundary.** No command above dispatches a model or starts the native live runner. A new live study must create a new prospective run specification with source/task/model/threshold/budget identity and its own attempts. Current authentication, account/quota guards, admission, replay and infrastructure requirements still apply. Charges depend on the selected route and provider; subscription usage is not an invoice. A new response or timing sample can differ even when the source and inputs are unchanged. Do not combine a new run with old successes or repeat until a preferred answer appears.

An agent reviewing this study should report: artifact commit and input hashes; selected mode; numerical match or exact mismatch; denominator and source grouping; whether raw parsing, private execution closure, live inference or human replay were actually performed. A successful offline reconstruction answers a narrower, useful question: **do the released observations produce the released numerical conclusions under the released analysis code?**
