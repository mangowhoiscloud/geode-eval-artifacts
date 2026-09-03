#!/usr/bin/env python3
# ruff: noqa: E501, S603
"""Render the result-first, paper-style v6 Terminal-Bench evidence film."""

from __future__ import annotations

import base64
import hashlib
import html
import importlib.util
import json
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "recording" / "public"
FIGURES = ROOT / "recording" / "figures-v6"
ASSETS = ROOT / "recording" / "assets"


def load_v3():
    path = ROOT / "render-evidence-video-v3.py"
    spec = importlib.util.spec_from_file_location("geode_evidence_v3", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load renderer: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V3 = load_v3()
HTMLS = {lang: PUBLIC / f"terminalbench21-geode-vs-native-evidence-v6-{lang}.html" for lang in ("ko", "en")}
VIDEOS = {lang: PUBLIC / f"terminalbench21-geode-vs-native-evidence-v6-{lang}.mp4" for lang in ("ko", "en")}
COMBINED_VIDEO = PUBLIC / "terminalbench21-geode-vs-native-evidence-v6-ko-en.mp4"
THUMBNAIL = PUBLIC / "terminalbench21-geode-vs-native-thumbnail-v6.png"
YOUTUBE_METADATA = PUBLIC / "terminalbench21-geode-vs-native-youtube-v6.md"
RECEIPT = PUBLIC / "video-v6.receipt.json"
AMENDMENT = ROOT / "publication-amendment-video-v6.receipt.json"
PUBLICATION = ROOT / "publication-v6.json"
PRIOR_PUBLICATION_REVISION = "fe1fbfe366ddd7ab3907b1217a13f24eda8f4130"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def data_url(path: Path) -> str:
    mime = "image/svg+xml" if path.suffix == ".svg" else "image/png"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def figure(name: str, lang: str, alt: str) -> str:
    return f'<img class="paper-figure" src="{data_url(FIGURES / f"{name}-{lang}.png")}" alt="{html.escape(alt)}">'


def page(
    section: str,
    ko_title: str,
    en_title: str,
    ko_kicker: str,
    en_kicker: str,
    ko_body: str,
    en_body: str,
    duration: float = 9.0,
    ko_badge: str = "파생 프레젠테이션 · 점수 권한 없음",
    en_badge: str = "Derived presentation · no score authority",
) -> dict[str, object]:
    return {
        "section": section,
        "ko": {"title": ko_title, "kicker": ko_kicker, "body": ko_body, "badge": ko_badge},
        "en": {"title": en_title, "kicker": en_kicker, "body": en_body, "badge": en_badge},
        "duration": duration,
    }


def task_families(lang: str) -> str:
    ko = lang == "ko"
    names = [
        ("셸 · 자동화", "write-compressor · headless-terminal"),
        ("빌드 · 디버깅", "build-pov-ray · compile-compcert · fix-ocaml-gc"),
        ("네트워크 · 서비스", "kv-store-grpc · pypi-server · mailman"),
        ("DB · 데이터 복구", "sqlite-db-truncate · db-wal-recovery · data-merger"),
        ("ML · 추론", "torch parallelism · hf-model-inference · model recovery"),
        ("과학 · 최적화", "dna/protein assembly · raman-fitting · portfolio-optimization"),
        ("미디어 · 추출", "video-processing · extract-moves-from-video · code-from-image"),
        ("보안 · 포렌식", "openssl · vulnerability · cryptanalysis · password recovery"),
    ] if ko else [
        ("Shell · automation", "write-compressor · headless-terminal"),
        ("Build · debugging", "build-pov-ray · compile-compcert · fix-ocaml-gc"),
        ("Network · services", "kv-store-grpc · pypi-server · mailman"),
        ("DB · recovery", "sqlite-db-truncate · db-wal-recovery · data-merger"),
        ("ML · inference", "torch parallelism · hf-model-inference · model recovery"),
        ("Science · optimization", "dna/protein assembly · raman-fitting · portfolio-optimization"),
        ("Media · extraction", "video-processing · extract-moves-from-video · code-from-image"),
        ("Security · forensics", "openssl · vulnerability · cryptanalysis · password recovery"),
    ]
    offsets = (-13, -115, -215, -314, -404, -495, -579, -659)
    items = "".join(
        f'<div class="family"><span class="family-icon" style="--icon-x:{offset}px"></span><div><b>{index:02d}</b><strong>{name}</strong><small>{examples}</small></div></div>'
        for index, ((name, examples), offset) in enumerate(zip(names, offsets), 1)
    )
    note = "분석자 분류이며 공식 taxonomy가 아닙니다." if ko else "Analyst-defined groups, not an official taxonomy."
    return f'<div class="families">{items}</div><p class="source-note">89 tasks × 5 repetitions × 2 arms = 890 intended cells · {note}</p>'


def build_pages(lang: str) -> list[dict[str, object]]:
    ko = lang == "ko"
    fig = lambda name, alt: figure(name, lang, alt)
    pages = [
        page(
            "RESULT",
            "동일 모델, 다른 하네스",
            "Same model, different harness",
            "Terminal-Bench 2.1 · 양쪽 모두 유효한 공통 429셀",
            "Terminal-Bench 2.1 · 429 cells valid in both arms",
            '<div class="cover"><div class="answer"><b>+8</b><span>GEODE 통과 셀</span><small>339/429 대 331/429 · +1.86 pp</small></div><div class="claim"><p>GEODE는 같은 모델을 사용한 native Codex보다 공통 셀 8개를 더 통과했습니다.</p><p class="limit">다만 태스크 방향은 16 대 16으로 갈렸고, full-suite primary는 측정할 수 없습니다.</p></div></div>',
            '<div class="cover"><div class="answer"><b>+8</b><span>GEODE passes</span><small>339/429 vs 331/429 · +1.86 pp</small></div><div class="claim"><p>GEODE passed eight more exact-common cells than native Codex with the same model.</p><p class="limit">But task directions split 16 to 16, and the full-suite primary is not measurable.</p></div></div>',
            11,
        ),
        page(
            "ABSTRACT",
            "세 문장으로 먼저 답합니다",
            "The result in three sentences",
            "관측값, 이질성, 해석 경계를 분리합니다",
            "Separate the observation, heterogeneity, and claim boundary",
            '<ol class="claims"><li><b>관측</b><span>공통 429셀에서 GEODE 79.02%, Codex 77.16%였습니다.</span></li><li><b>이질성</b><span>87개 실행 가능 태스크 중 GEODE 우세 16개, 동률 55개, Codex 우세 16개였습니다.</span></li><li><b>판정</b><span>작은 로컬 우세는 보였지만, 일반적 하네스 우월성이나 공식 순위로 확대할 근거는 없습니다.</span></li></ol>',
            '<ol class="claims"><li><b>Observation</b><span>On 429 exact-common cells, GEODE scored 79.02% and Codex 77.16%.</span></li><li><b>Heterogeneity</b><span>Across 87 runnable tasks, 16 favored GEODE, 55 tied, and 16 favored Codex.</span></li><li><b>Decision</b><span>A modest local edge was observed; it does not establish general harness superiority or an official rank.</span></li></ol>',
            10,
        ),
        page("RESULT", "공통 셀에서만 직접 비교합니다", "Direct comparison uses only exact-common cells", "보조 수치는 분모가 다릅니다", "Secondary metrics have different denominators", fig("pass-rate-comparison", "공통 셀과 보조 범위의 GEODE 및 Codex 통과율"), fig("pass-rate-comparison", "GEODE and Codex pass rates on exact-common and secondary coverage"), 10),
        page("HETEROGENEITY", "우세 태스크 수는 같았습니다", "Task wins were evenly split", "셀 평균의 +1.86 pp를 태스크 단위로 다시 봅니다", "Re-examine the +1.86 pp cell mean at task level", fig("task-heterogeneity", "태스크별 통과율 차이와 태스크 클러스터 부트스트랩"), fig("task-heterogeneity", "Task-level pass-rate deltas and task-cluster bootstrap"), 11),
        page(
            "CONTRIBUTION",
            "이 실행의 성취는 점수 하나가 아닙니다",
            "The accomplishment is more than one score",
            "비교 가능성, 계보, 재생성, 공개 검증을 함께 남겼습니다",
            "It preserves comparability, lineage, replay, and publication checks",
            '<div class="metrics"><div><b>429</b><strong>동일 조건 공통 쌍</strong><span>같은 task·repetition에서 양쪽 모두 유효</span></div><div><b>936</b><strong>모델 시도 계보</strong><span>원본과 76개 보충 시도를 append-only로 보존</span></div><div><b>856</b><strong>trajectory 기반 replay</strong><span>행동 증거를 score 권한과 분리</span></div><div><b>890</b><strong>전체 관찰 인덱스</strong><span>실행·receipt·제외 상태를 빠짐없이 표기</span></div></div>',
            '<div class="metrics"><div><b>429</b><strong>Exact-common pairs</strong><span>Both arms valid for the same task and repetition</span></div><div><b>936</b><strong>Model-attempt lineage</strong><span>Originals and 76 supplements preserved append-only</span></div><div><b>856</b><strong>Trajectory-derived replays</strong><span>Behavior evidence separated from score authority</span></div><div><b>890</b><strong>Full observation index</strong><span>Executed, receipt, and exclusion states are explicit</span></div></div>',
            11,
        ),
        page(
            "QUESTION",
            "하네스가 같은 모델의 성과를 바꾸는가?",
            "Does the harness change the same model's outcome?",
            "모델 효과와 실행기 효과를 가능한 범위에서 분리합니다",
            "Separate model effects from runtime effects where the protocol permits",
            '<div class="question"><p>같은 <b>gpt-5.6-sol · max</b>가 동일 task·verifier·timeout에서 실행될 때, GEODE runtime과 native Codex CLI의 verifier 통과율은 달라지는가?</p><div class="equation"><span>고정</span><b>model · task · verifier · budget</b><i>→</i><span>변수</span><b>runtime harness</b></div><small>로컬 paired diagnostic이며 공식 Terminal-Bench 제출과 동등하지 않습니다.</small></div>',
            '<div class="question"><p>When the same <b>gpt-5.6-sol · max</b> runs under the same task, verifier, and timeout, do GEODE and native Codex CLI produce different verifier pass rates?</p><div class="equation"><span>fixed</span><b>model · task · verifier · budget</b><i>→</i><span>variable</span><b>runtime harness</b></div><small>This is a local paired diagnostic, not an official Terminal-Bench submission.</small></div>',
            10,
        ),
        page("SUITE", "Terminal-Bench 2.1은 실제 터미널 작업을 측정합니다", "Terminal-Bench 2.1 measures real terminal work", "동결한 89개 task ID를 여덟 작업군으로 설명합니다", "Eight analyst-defined families explain the frozen 89 task IDs", task_families("ko"), task_families("en"), 11),
        page(
            "UNITS",
            "cell이 비교의 최소 단위입니다",
            "The cell is the smallest comparison unit",
            "task, repetition, arm을 섞지 않습니다",
            "Task, repetition, and arm remain explicit",
            '<div class="unit-line"><span>task</span><i>×</i><span>repetition</span><i>×</i><span>arm</span><b>= cell</b></div><dl class="definitions"><div><dt>attempt</dt><dd>한 cell을 채우기 위한 실제 모델 시도입니다. 인프라 무효면 사전 등록된 보충 시도가 뒤따를 수 있습니다.</dd></div><div><dt>selected cell</dt><dd>분석에 채택된 최종 시도입니다. 유효한 실패와 timeout은 0점으로 남습니다.</dd></div><div><dt>exact-common</dt><dd>같은 task·repetition에서 양쪽 arm이 모두 유효한 cell 쌍입니다.</dd></div></dl>',
            '<div class="unit-line"><span>task</span><i>×</i><span>repetition</span><i>×</i><span>arm</span><b>= cell</b></div><dl class="definitions"><div><dt>attempt</dt><dd>An actual model run used to fill a cell. A prospectively registered supplement may follow an infrastructure-invalid attempt.</dd></div><div><dt>selected cell</dt><dd>The terminal attempt selected for analysis. Valid failures and timeouts remain zero.</dd></div><div><dt>exact-common</dt><dd>A task-repetition pair for which both arms have valid selected cells.</dd></div></dl>',
            11,
        ),
        page(
            "DESIGN",
            "공유 조건을 동결한 뒤 runtime만 갈랐습니다",
            "Shared conditions were frozen before runtime assignment",
            "89 tasks · 5 repetitions · two arms · zero automatic retries",
            "89 tasks · 5 repetitions · two arms · zero automatic retries",
            '<div class="design"><div class="shared"><b>공유 조건</b><span>terminal-bench/terminal-bench-2-1@6 · gpt-5.6-sol · max · 공식 task image · verifier · task별 timeout/resource · OpenAI subscription</span></div><div class="fork"><div><b>GEODE</b><span>GEODE AgenticLoop와 도구 실행 경로</span></div><i>같은 cell key</i><div><b>native Codex</b><span>Harbor Codex agent의 native CLI 경로</span></div></div><p>반복 pairing은 workload 정렬입니다. Harbor 0.22.0에는 양쪽에 공유되는 seed 제어가 없습니다.</p></div>',
            '<div class="design"><div class="shared"><b>Shared conditions</b><span>terminal-bench/terminal-bench-2-1@6 · gpt-5.6-sol · max · official task image · verifier · task timeout/resource · OpenAI subscription</span></div><div class="fork"><div><b>GEODE</b><span>GEODE AgenticLoop and tool path</span></div><i>same cell key</i><div><b>native Codex</b><span>Harbor Codex agent native CLI path</span></div></div><p>Repetition pairing aligns workload; Harbor 0.22.0 does not expose a shared seed control across both arms.</p></div>',
            11,
        ),
        page(
            "ISOLATION",
            "Harbor가 trial을 격리하고 verifier를 실행했습니다",
            "Harbor isolated each trial and ran the verifier",
            "호스트 관찰, trial 실행, 점수 판정을 분리합니다",
            "Separate host observation, trial execution, and scoring",
            '<div class="lane"><div><b>arm64 host</b><span>disk · Docker · subscription auth</span></div><i>→</i><div><b>Harbor 0.22.0</b><span>manifest · concurrency 2 · zero retry</span></div><i>→</i><div><b>trial container</b><span>GEODE 또는 native Codex</span></div><i>→</i><div><b>verifier</b><span>reward.txt · result.json</span></div></div><p class="under">Observer PTY는 이 과정을 관찰했지만 점수는 만들지 않습니다.</p>',
            '<div class="lane"><div><b>arm64 host</b><span>disk · Docker · subscription auth</span></div><i>→</i><div><b>Harbor 0.22.0</b><span>manifest · concurrency 2 · zero retry</span></div><i>→</i><div><b>trial container</b><span>GEODE or native Codex</span></div><i>→</i><div><b>verifier</b><span>reward.txt · result.json</span></div></div><p class="under">Observer PTY records the procedure; it does not create the score.</p>',
            10,
        ),
        page(
            "AUTHORITY",
            "점수와 행동, 절차의 증거 권한이 다릅니다",
            "Score, behavior, and procedure have different authority",
            "영상이 verifier 결과를 대신하지 않습니다",
            "The video never substitutes for verifier output",
            '<div class="authority"><div><b>점수</b><strong>Harbor result + verifier receipt</strong><span>numerator와 denominator의 유일한 권한</span></div><div><b>행동</b><strong>ATIF trajectory + derived cast</strong><span>도구 사용과 상태 전이를 재검토</span></div><div><b>절차</b><strong>observer-side PTY + 영상</strong><span>배치 실행과 운영 절차를 확인</span></div></div>',
            '<div class="authority"><div><b>Score</b><strong>Harbor result + verifier receipt</strong><span>Sole authority for numerator and denominator</span></div><div><b>Behavior</b><strong>ATIF trajectory + derived cast</strong><span>Review tool use and state transitions</span></div><div><b>Procedure</b><strong>observer-side PTY + video</strong><span>Verify batch execution and operator procedure</span></div></div>',
            10,
        ),
        page(
            "LINEAGE",
            "원본 시도는 보충 실행 뒤에도 사라지지 않습니다",
            "Original attempts remain after supplements",
            "append-only 계보가 selected cell을 설명합니다",
            "Append-only lineage explains every selected cell",
            '<div class="lineage"><span><b>attempt</b><small>936 model rows</small></span><i>→</i><span><b>trajectory</b><small>tool and state events</small></span><i>→</i><span><b>verifier receipt</b><small>reward or invalid class</small></span><i>→</i><span><b>selected outcome</b><small>cell authority</small></span><i>→</i><span><b>analysis</b><small>aggregate views</small></span></div><p>인프라 무효 원본과 76개 보충 시도의 parent 관계를 함께 보존했습니다.</p>',
            '<div class="lineage"><span><b>attempt</b><small>936 model rows</small></span><i>→</i><span><b>trajectory</b><small>tool and state events</small></span><i>→</i><span><b>verifier receipt</b><small>reward or invalid class</small></span><i>→</i><span><b>selected outcome</b><small>cell authority</small></span><i>→</i><span><b>analysis</b><small>aggregate views</small></span></div><p>Parent links preserve infrastructure-invalid originals alongside 76 supplement attempts.</p>',
            10,
        ),
        page("ACCOUNTING", "890개 의도 셀을 네 상태로 추적했습니다", "All 890 intended cells remain accounted for", "제외, 인프라 무효, 유효 0점을 섞지 않습니다", "Exclusions, invalid cells, and valid zeroes are not pooled", fig("measurement-cascade", "890개 의도 셀에서 통과 셀까지의 측정 흐름"), fig("measurement-cascade", "Measurement flow from 890 intended cells to passes"), 10),
        page("PAIRED RESULT", "+8셀은 paired outcome에서 직접 확인됩니다", "The +8-cell edge is visible in paired outcomes", "53 GEODE-only 대 45 Codex-only", "53 GEODE-only versus 45 Codex-only", fig("paired-outcomes", "429개 공통 셀의 paired outcome"), fig("paired-outcomes", "Paired outcomes for 429 exact-common cells"), 10),
        page("TASK EFFECT", "평균은 반대 방향의 큰 태스크 효과를 숨깁니다", "The mean hides large opposing task effects", "상·하위 태스크의 공통 셀 통과율 차이", "Exact-common pass-rate deltas for the largest reversals", fig("task-extremes", "GEODE와 Codex의 태스크별 극단 차이"), fig("task-extremes", "Largest task-level reversals between GEODE and Codex"), 11),
        page(
            "INTERPRETATION",
            "GEODE의 우세는 작고 태스크 의존적입니다",
            "GEODE's observed edge is modest and task-dependent",
            "관측값과 일반화 주장을 구분합니다",
            "Separate the observed result from generalization",
            '<div class="interpret"><p><b>확인된 관측</b><span>공통 셀 +8, +1.86 pp</span></p><p><b>태스크 균형 평균</b><span>+1.26 pp</span></p><p><b>태스크 클러스터 bootstrap</b><span>95% percentile interval −5.40~+8.05 pp · 0 포함</span></p><p class="decision"><b>결론</b><span>이 런에서는 GEODE가 앞섰지만, 효과는 일부 태스크의 큰 역전에 좌우됩니다.</span></p></div>',
            '<div class="interpret"><p><b>Confirmed observation</b><span>+8 exact-common cells, +1.86 pp</span></p><p><b>Task-balanced mean</b><span>+1.26 pp</span></p><p><b>Task-cluster bootstrap</b><span>95% percentile interval −5.40 to +8.05 pp · includes zero</span></p><p class="decision"><b>Conclusion</b><span>GEODE led in this run, but the effect depends on a few large task reversals.</span></p></div>',
            11,
        ),
        page("FAILURES", "실패는 0점과 인프라 무효로 먼저 나뉩니다", "Failures first split into valid zeroes and invalid attempts", "서로 다른 단위와 분모를 별도 도표로 제시합니다", "Different units and denominators appear in separate panels", fig("failure-decomposition", "유효 0점과 인프라 무효 시도의 구성"), fig("failure-decomposition", "Composition of valid zeroes and infrastructure-invalid attempts"), 11),
        page(
            "FAILURE TRACE",
            "영상 처리 태스크는 시간 예산 경계를 드러냈습니다",
            "A video task exposed the time-budget boundary",
            "extract-moves-from-video의 선택 결과를 계보와 함께 읽습니다",
            "Read selected outcomes together with attempt lineage",
            '<div class="trace"><div><b>GEODE · repetitions 1–5</b><span>다섯 시도 모두 1,800초 agent budget을 소진했습니다.</span><strong>canonical-agent-timeout → valid selected zero</strong></div><div><b>native · common repetitions</b><span>repetitions 2와 4는 통과했고 1과 5는 canonical timeout이었습니다.</span><strong>2/4 exact-common passes</strong></div><div><b>native · repetition 3</b><span>원본과 허용된 보충이 AgentSetupTimeoutError로 끝났습니다.</span><strong>infrastructure-invalid → unresolved</strong></div></div><p class="source-note">timeout stack 하나만으로 전체 30분을 provider 대기로 단정하지 않았습니다.</p>',
            '<div class="trace"><div><b>GEODE · repetitions 1–5</b><span>All five attempts exhausted the 1,800-second agent budget.</span><strong>canonical-agent-timeout → valid selected zero</strong></div><div><b>native · common repetitions</b><span>Repetitions 2 and 4 passed; 1 and 5 reached canonical timeout.</span><strong>2/4 exact-common passes</strong></div><div><b>native · repetition 3</b><span>The original and authorized supplement ended with AgentSetupTimeoutError.</span><strong>infrastructure-invalid → unresolved</strong></div></div><p class="source-note">A timeout stack alone was not treated as proof that all 30 minutes were provider wait.</p>',
            12,
        ),
        page(
            "EXCLUSIONS",
            "20개 셀은 모델 호출 전에 대칭 제외했습니다",
            "Twenty cells were symmetrically excluded before model calls",
            "두 task ID는 arm64 호스트에서 공식 amd64 verifier oracle을 통과하지 못했습니다",
            "Two task IDs failed official amd64 verifier oracle preflight on the arm64 host",
            '<div class="exclusions"><div><code>terminal-bench/bn-fit-modify</code><b>5 repetitions × 2 arms = 10 cells</b><p>공식 amd64 컨테이너의 scipy.stats import가 Rosetta 환경에서 완료되지 않았습니다. 원본 oracle은 3,600초를 소진했고 동일 조건 재현도 멈췄습니다. 사전 등록한 OPENBLAS_NUM_THREADS=1 calibration도 실패해 채택하지 않았습니다.</p></div><div><code>terminal-bench/tune-mjcf</code><b>5 repetitions × 2 arms = 10 cells</b><p>공식 amd64 컨테이너가 변경하지 않은 MuJoCo verifier dependency를 import하는 중 fatal illegal-instruction으로 종료되어 pytest collection에 도달하지 못했습니다.</p></div></div><p class="source-note">제외 셀은 0점도 통과도 아닙니다. x86_64 Linux에서 별도 보조 연구가 필요합니다.</p>',
            '<div class="exclusions"><div><code>terminal-bench/bn-fit-modify</code><b>5 repetitions × 2 arms = 10 cells</b><p>The official amd64 container could not complete its scipy.stats import under Rosetta. The original oracle exhausted 3,600 seconds, a same-contract reproduction stalled, and a preregistered OPENBLAS_NUM_THREADS=1 calibration was rejected.</p></div><div><code>terminal-bench/tune-mjcf</code><b>5 repetitions × 2 arms = 10 cells</b><p>The official amd64 container hit a fatal illegal-instruction while importing the unchanged MuJoCo verifier dependency, before pytest collection.</p></div></div><p class="source-note">Excluded cells are neither zeroes nor passes. A separate x86_64 Linux study is required.</p>',
            13,
        ),
        page(
            "UNRESOLVED",
            "native Codex의 6셀은 보충 한도 뒤에도 미해소입니다",
            "Six native Codex cells remained unresolved after supplement caps",
            "primary denominator를 억지로 채우지 않았습니다",
            "The primary denominator was not force-filled",
            '<div class="unresolved"><code>torch-pipeline-parallelism · repetitions 1, 4</code><code>financial-document-processor · repetition 5</code><code>extract-moves-from-video · repetition 3</code><code>sqlite-with-gcov · repetition 5</code><code>constraints-scheduling · repetition 4</code></div><p>이 셀들은 0점이 아니라 infrastructure-invalid입니다. 따라서 full-suite primary는 not measurable입니다.</p>',
            '<div class="unresolved"><code>torch-pipeline-parallelism · repetitions 1, 4</code><code>financial-document-processor · repetition 5</code><code>extract-moves-from-video · repetition 3</code><code>sqlite-with-gcov · repetition 5</code><code>constraints-scheduling · repetition 4</code></div><p>These cells are infrastructure-invalid, not zeroes. Therefore the full-suite primary is not measurable.</p>',
            11,
        ),
        page(
            "REPLAY",
            "890-cell 관찰 범위와 재생 가능 범위를 구분했습니다",
            "The 890-cell observation index is broader than replay coverage",
            "trajectory가 있는 곳만 terminal replay를 재구성합니다",
            "Terminal replay is reconstructed only where trajectory coverage exists",
            '<div class="replay"><div><b>856</b><span>source trajectories → reconstructed casts</span></div><div><b>890</b><span>observation index = 834 ATIF detail + 36 receipt events + 20 exclusion cards</span></div><div><b>67</b><span>observer PTY segments · batch/operator procedure evidence</span></div></div><p>derived cast는 raw PTY가 아니며, receipt와 exclusion은 terminal 동작을 꾸며내지 않습니다.</p>',
            '<div class="replay"><div><b>856</b><span>source trajectories → reconstructed casts</span></div><div><b>890</b><span>observation index = 834 ATIF detail + 36 receipt events + 20 exclusion cards</span></div><div><b>67</b><span>observer PTY segments · batch/operator procedure evidence</span></div></div><p>A derived cast is not raw PTY; receipt and exclusion cards do not invent terminal behavior.</p>',
            11,
        ),
        page(
            "PUBLICATION",
            "공개는 raw 복제가 아니라 검증된 allowlist입니다",
            "Publication is a verified allowlist, not a raw dump",
            "canonical ledger에서 파생물을 만든 뒤 원격 바이트까지 되읽습니다",
            "Derived views are built from the canonical ledger and read back byte-for-byte",
            '<div class="publish"><span><b>canonical</b><small>attempts · results · receipts · outcomes</small></span><i>→</i><span><b>derive</b><small>analysis · figures · replay index · video</small></span><i>→</i><span><b>scan</b><small>schema · hash · secret · PII · local path</small></span><i>→</i><span><b>publish</b><small>append-only PR · immutable commit</small></span><i>→</i><span><b>read back</b><small>remote bytes and SHA-256</small></span></div>',
            '<div class="publish"><span><b>canonical</b><small>attempts · results · receipts · outcomes</small></span><i>→</i><span><b>derive</b><small>analysis · figures · replay index · video</small></span><i>→</i><span><b>scan</b><small>schema · hash · secret · PII · local path</small></span><i>→</i><span><b>publish</b><small>append-only PR · immutable commit</small></span><i>→</i><span><b>read back</b><small>remote bytes and SHA-256</small></span></div>',
            10,
        ),
        page(
            "LIMITS",
            "이 결과가 말하지 않는 것도 명시합니다",
            "The result also states what it cannot establish",
            "정확한 비교 가능성 경계",
            "Exact comparability boundary",
            '<ul class="limits"><li>공식 Terminal-Bench leaderboard 점수나 순위가 아닙니다.</li><li>full-suite 445셀/arm primary metric은 측정할 수 없습니다.</li><li>실행이 여러 날과 credential principal 전환을 걸쳐 시간 효과를 분리할 수 없습니다.</li><li>공유 seed 제어가 없어 repetition pairing은 동일 난수 보장이 아닙니다.</li><li>태스크 클러스터 bootstrap 구간은 0을 포함합니다.</li></ul>',
            '<ul class="limits"><li>Not an official Terminal-Bench leaderboard score or rank.</li><li>The 445-cell-per-arm full-suite primary is not measurable.</li><li>The run spans days and credential-principal transitions, so temporal effects are not separable.</li><li>No shared seed control; repetition pairing does not guarantee shared randomness.</li><li>The task-cluster bootstrap interval includes zero.</li></ul>',
            11,
        ),
        page(
            "CONCLUSION",
            "성능 우세보다 더 강한 성취는 검증 가능한 비교입니다",
            "The stronger accomplishment is a verifiable comparison",
            "관측된 +8셀을 보존하되, 그보다 큰 주장은 닫습니다",
            "Preserve the observed +8 cells and close larger claims",
            '<div class="closing"><p><b>결과</b><span>GEODE 339/429, Codex 331/429</span></p><p><b>인사이트</b><span>우세 태스크 수는 같고, 일부 큰 역전이 평균을 만들었습니다.</span></p><p><b>성취</b><span>890셀 상태, 936시도 계보, verifier 권한, replay와 공개 검증을 하나의 재현 가능한 증거 체계로 연결했습니다.</span></p><p><b>다음 검증</b><span>x86_64에서 제외 20셀을 별도 실행하고, 독립 반복으로 효과의 안정성을 확인합니다.</span></p></div>',
            '<div class="closing"><p><b>Result</b><span>GEODE 339/429, Codex 331/429</span></p><p><b>Insight</b><span>Task wins were even; a few large reversals created the mean edge.</span></p><p><b>Accomplishment</b><span>The work joins 890-cell accounting, 936-attempt lineage, verifier authority, replay, and publication checks into one reproducible evidence system.</span></p><p><b>Next test</b><span>Run the 20 excluded cells on x86_64 and test stability with an independent replication.</span></p></div>',
            12,
        ),
    ]
    return [{"section": item["section"], "duration": item["duration"], **item[lang]} for item in pages]


SPRITE = data_url(ASSETS / "terminalbench-icon-strip-transparent-v5.png")
GEODI = data_url(ASSETS / "geodi-dot.svg")
HARBOR = data_url(ASSETS / "harbor-wordmark-dark.png")

CSS = f"""
:root{{--ink:#171717;--mid:#6f6f6b;--line:#d8d8d3;--soft:#f4f4f0;--geode:#137a3a;--codex:#285a84;--rust:#a84a3a}}
*{{box-sizing:border-box}}html,body{{margin:0;background:white;color:var(--ink);font-family:"Apple SD Gothic Neo","Helvetica Neue",Arial,sans-serif}}body{{overflow:hidden}}.slide{{display:none;width:1920px;height:1080px;padding:52px 110px 46px;background:white;flex-direction:column}}.slide.active{{display:flex}}.top{{height:54px;display:flex;align-items:flex-start;border-bottom:1px solid var(--ink);font-size:16px}}.label{{display:flex;gap:18px}}.label b{{font-family:Menlo,monospace;font-weight:500}}.label span{{color:var(--mid)}}.run{{margin-left:auto;color:var(--mid)}}.kicker{{margin:28px 0 6px;font-size:21px;color:var(--mid)}}h1{{font-size:52px;line-height:1.08;letter-spacing:-1.4px;margin:0 0 24px;font-weight:650}}.body{{flex:1;min-height:0;display:flex;flex-direction:column;justify-content:center}}.footer{{height:42px;border-top:1px solid var(--ink);padding-top:13px;display:flex;font-size:15px}}.footer b{{font-family:Menlo,monospace;font-weight:500}}.footer span{{margin-left:auto;color:var(--mid)}}.brand{{position:absolute;right:110px;bottom:82px;display:flex;align-items:center;gap:18px;opacity:.12}}.brand img:first-child{{width:38px;height:38px}}.brand img:last-child{{width:128px;height:auto}}.paper-figure{{width:100%;height:690px;object-fit:contain;display:block}}.cover{{display:grid;grid-template-columns:.65fr 1.35fr;gap:90px;align-items:center}}.answer{{display:flex;flex-direction:column}}.answer b{{font-size:170px;line-height:.9;color:var(--geode);letter-spacing:-8px}}.answer span{{font-size:35px;margin-top:18px}}.answer small{{font:18px Menlo,monospace;color:var(--mid);margin-top:18px}}.claim{{border-left:1px solid var(--ink);padding-left:60px}}.claim p{{font-size:39px;line-height:1.45;margin:0}}.claim .limit{{font-size:25px;color:var(--mid);margin-top:38px}}.claims{{list-style:none;padding:0;margin:0;border-top:1px solid var(--ink)}}.claims li{{display:grid;grid-template-columns:220px 1fr;gap:45px;padding:32px 0;border-bottom:1px solid var(--line)}}.claims b{{font:18px Menlo,monospace;color:var(--geode)}}.claims span{{font-size:30px;line-height:1.35}}.metrics{{display:grid;grid-template-columns:repeat(4,1fr);gap:0;border-top:1px solid var(--ink)}}.metrics div{{padding:34px 30px 20px 0;border-right:1px solid var(--line);min-height:370px;display:flex;flex-direction:column}}.metrics div+div{{padding-left:30px}}.metrics div:last-child{{border-right:0}}.metrics b{{font-size:92px;line-height:1;color:var(--geode)}}.metrics strong{{font-size:25px;margin-top:30px}}.metrics span{{font-size:20px;line-height:1.45;color:var(--mid);margin-top:auto}}.question p{{font-size:37px;line-height:1.45;max-width:1500px;margin:0}}.question>small{{display:block;font-size:18px;color:var(--mid);margin-top:55px}}.equation{{display:grid;grid-template-columns:110px 1.4fr 80px 100px 1fr;align-items:center;margin-top:70px;border-top:1px solid var(--ink);border-bottom:1px solid var(--line);padding:30px 0}}.equation span{{font:16px Menlo,monospace;color:var(--mid)}}.equation b{{font-size:25px}}.equation i{{font-style:normal;font-size:28px}}.families{{display:grid;grid-template-columns:repeat(4,1fr);gap:0 34px}}.family{{display:grid;grid-template-columns:76px 1fr;gap:14px;align-items:center;min-height:150px;border-top:1px solid var(--line)}}.family-icon{{display:block;width:72px;height:72px;background-image:url({SPRITE});background-repeat:no-repeat;background-size:auto 72px;background-position:var(--icon-x) center}}.family div{{display:flex;flex-direction:column;gap:5px}}.family b{{font:13px Menlo,monospace;color:var(--mid)}}.family strong{{font-size:21px}}.family small{{font:12px Menlo,monospace;color:var(--mid);line-height:1.35}}.source-note{{font-size:16px;color:var(--mid);margin:22px 0 0}}.unit-line{{display:flex;align-items:center;justify-content:center;gap:32px;font:28px Menlo,monospace;margin-bottom:65px}}.unit-line span{{border-bottom:1px solid var(--ink);padding:14px 8px}}.unit-line i{{font-style:normal;color:var(--mid)}}.unit-line b{{color:var(--geode)}}.definitions{{margin:0;border-top:1px solid var(--ink)}}.definitions div{{display:grid;grid-template-columns:260px 1fr;border-bottom:1px solid var(--line);padding:22px 0}}.definitions dt{{font:18px Menlo,monospace;color:var(--geode)}}.definitions dd{{font-size:22px;margin:0}}.design .shared{{display:grid;grid-template-columns:220px 1fr;padding:25px 0;border-top:1px solid var(--ink);border-bottom:1px solid var(--line)}}.design .shared b{{font:17px Menlo,monospace;color:var(--geode)}}.design .shared span{{font-size:20px}}.fork{{display:grid;grid-template-columns:1fr 170px 1fr;align-items:center;margin-top:70px}}.fork div{{padding:28px 0;border-top:1px solid var(--ink)}}.fork b{{font-size:34px;display:block}}.fork span{{font-size:22px;color:var(--mid)}}.fork i{{text-align:center;font:14px Menlo,monospace;color:var(--mid)}}.design p{{font-size:18px;color:var(--mid);margin-top:65px}}.lane{{display:grid;grid-template-columns:1fr 50px 1fr 50px 1fr 50px 1fr;align-items:center}}.lane div{{min-height:210px;border-top:2px solid var(--ink);padding:30px 10px}}.lane div:last-child{{border-top-color:var(--geode)}}.lane b{{font-size:29px;display:block}}.lane span{{font-size:20px;color:var(--mid);display:block;margin-top:28px;line-height:1.45}}.lane i{{text-align:center;font-style:normal;font-size:27px;color:var(--mid)}}.under{{font-size:21px;margin-top:80px}}.authority{{display:grid;grid-template-columns:repeat(3,1fr);border-top:1px solid var(--ink)}}.authority div{{min-height:390px;padding:35px 36px 25px 0;border-right:1px solid var(--line);display:flex;flex-direction:column}}.authority div+div{{padding-left:36px}}.authority div:last-child{{border-right:0}}.authority b{{font:16px Menlo,monospace;color:var(--geode)}}.authority strong{{font-size:30px;margin-top:30px}}.authority span{{font-size:21px;color:var(--mid);margin-top:auto}}.lineage,.publish{{display:grid;grid-template-columns:repeat(9,auto);align-items:center}}.lineage span,.publish span{{min-height:190px;border-top:1px solid var(--ink);padding:25px 8px;display:flex;flex-direction:column}}.lineage b,.publish b{{font-size:24px}}.lineage small,.publish small{{font:14px Menlo,monospace;color:var(--mid);margin-top:auto;line-height:1.45}}.lineage i,.publish i{{font-style:normal;font-size:25px;padding:0 12px;color:var(--mid)}}.lineage+p{{font-size:20px;margin-top:65px}}.interpret{{border-top:1px solid var(--ink)}}.interpret p{{display:grid;grid-template-columns:370px 1fr;margin:0;padding:22px 0;border-bottom:1px solid var(--line)}}.interpret b{{font:17px Menlo,monospace;color:var(--mid)}}.interpret span{{font-size:27px}}.interpret .decision{{padding-top:34px}}.interpret .decision b{{color:var(--geode)}}.trace{{display:grid;grid-template-columns:repeat(3,1fr);border-top:1px solid var(--ink)}}.trace div{{min-height:380px;padding:30px 34px 20px 0;border-right:1px solid var(--line);display:flex;flex-direction:column}}.trace div+div{{padding-left:34px}}.trace div:last-child{{border-right:0}}.trace b{{font:16px Menlo,monospace;color:var(--mid)}}.trace span{{font-size:24px;line-height:1.45;margin-top:32px}}.trace strong{{font:15px Menlo,monospace;color:var(--rust);margin-top:auto}}.exclusions{{display:grid;grid-template-columns:1fr 1fr;border-top:1px solid var(--rust)}}.exclusions div{{padding:30px 38px 15px 0;border-right:1px solid var(--line)}}.exclusions div+div{{padding-left:38px;border-right:0}}.exclusions code{{font-size:24px}}.exclusions b{{font:15px Menlo,monospace;color:var(--rust);display:block;margin-top:18px}}.exclusions p{{font-size:20px;line-height:1.55;margin-top:30px}}.unresolved{{display:grid;grid-template-columns:1fr 1fr;border-top:1px solid var(--ink)}}.unresolved code{{font-size:19px;padding:28px 0;border-bottom:1px solid var(--line)}}.unresolved code:nth-child(odd){{border-right:1px solid var(--line)}}.unresolved code:nth-child(even){{padding-left:35px}}.unresolved+p{{font-size:25px;margin-top:60px}}.replay{{display:grid;grid-template-columns:repeat(3,1fr);border-top:1px solid var(--ink)}}.replay div{{min-height:320px;padding:32px 35px 20px 0;border-right:1px solid var(--line);display:flex;flex-direction:column}}.replay div+div{{padding-left:35px}}.replay div:last-child{{border-right:0}}.replay b{{font-size:82px;color:var(--geode)}}.replay span{{font:17px Menlo,monospace;color:var(--mid);margin-top:auto;line-height:1.55}}.replay+p{{font-size:20px;margin-top:50px}}.limits{{list-style:none;margin:0;padding:0;border-top:1px solid var(--ink)}}.limits li{{font-size:25px;padding:20px 0 20px 38px;border-bottom:1px solid var(--line);position:relative}}.limits li:before{{content:"";position:absolute;left:2px;top:32px;width:9px;height:9px;background:var(--rust)}}.closing{{border-top:1px solid var(--ink)}}.closing p{{display:grid;grid-template-columns:260px 1fr;margin:0;padding:20px 0;border-bottom:1px solid var(--line)}}.closing b{{font:17px Menlo,monospace;color:var(--geode)}}.closing span{{font-size:25px;line-height:1.35}}.nav-hint{{position:fixed;opacity:.01}}
"""


def render_html(pages: list[dict[str, object]], output: Path, language: str) -> None:
    articles = []
    for index, item in enumerate(pages):
        articles.append(
            f'<article class="slide" data-duration="{item["duration"]}"><div class="top"><div class="label"><b>v6</b><span>{html.escape(str(item["section"]))}</span></div><div class="run">Terminal-Bench 2.1 · same-model paired runtime</div></div><p class="kicker">{html.escape(str(item["kicker"]))}</p><h1>{html.escape(str(item["title"]))}</h1><div class="body">{item["body"]}</div><div class="footer"><b>{index + 1:02d} / {len(pages):02d}</b><span>{html.escape(str(item["badge"]))}</span></div><div class="brand"><img src="{GEODI}"><img src="{HARBOR}"></div></article>'
        )
    document = f'<!doctype html><html lang="{language}"><head><meta charset="utf-8"><meta name="viewport" content="width=1920,initial-scale=1"><title>GEODE Terminal-Bench Evidence v6</title><style>{CSS}</style></head><body>{"".join(articles)}<span class="nav-hint">← →</span><script>const slides=[...document.querySelectorAll(".slide")];const p=new URLSearchParams(location.search);let current=Math.max(0,Math.min(slides.length-1,Number(p.get("slide")||0)));function show(i){{slides.forEach((s,n)=>s.classList.toggle("active",n===i));current=i}}show(current);addEventListener("keydown",e=>{{if(e.key==="ArrowRight")show(Math.min(slides.length-1,current+1));if(e.key==="ArrowLeft")show(Math.max(0,current-1))}});</script></body></html>'
    output.write_text(document, encoding="utf-8")


def combine_videos() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="geode-evidence-v6-join-") as temporary:
        listing = Path(temporary) / "concat.txt"
        listing.write_text("".join(f"file '{VIDEOS[lang].as_posix()}'\n" for lang in ("ko", "en")), encoding="utf-8")
        subprocess.run(["/opt/homebrew/bin/ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", "-movflags", "+faststart", str(COMBINED_VIDEO)], check=True)
    return V3.probe_video(COMBINED_VIDEO)


def render_thumbnail() -> None:
    with tempfile.TemporaryDirectory(prefix="geode-v6-thumbnail-") as temporary:
        frame = Path(temporary) / "cover.png"
        subprocess.run([str(V3.CHROME), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files", "--force-device-scale-factor=1", "--window-size=1920,1080", "--run-all-compositor-stages-before-draw", "--virtual-time-budget=800", "--timeout=5000", f"--screenshot={frame}", f"{HTMLS['ko'].as_uri()}?slide=0"], check=True, capture_output=True, timeout=20)
        subprocess.run(["/opt/homebrew/bin/ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(frame), "-vf", "scale=1280:720", str(THUMBNAIL)], check=True)


def timestamp(seconds: float) -> str:
    minutes, whole = divmod(int(seconds), 60)
    return f"{minutes:02d}:{whole:02d}"


def write_youtube(pages_by_language: dict[str, list[dict[str, object]]]) -> None:
    lines = ["# GEODE vs native Codex on Terminal-Bench 2.1", "", "Same model, different harness. Korean first, then English.", "", "## Timeline", ""]
    elapsed = 0.0
    for language in ("ko", "en"):
        lines.append(f"{timestamp(elapsed)} {'한국어' if language == 'ko' else 'English'}")
        for index, item in enumerate(pages_by_language[language]):
            lines.append(f"{timestamp(elapsed)} {item['title']}")
            elapsed += float(item["duration"])
        lines.append("")
    lines.extend(["## Evidence boundary", "", "Harbor result and verifier receipts are score authority. Trajectories and derived casts are behavior evidence. Observer PTY and this film are procedure/presentation evidence. The full-suite primary is not measurable, and this is not an official leaderboard score.", ""])
    YOUTUBE_METADATA.write_text("\n".join(lines), encoding="utf-8")


def dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def publication_entry(path: Path) -> dict[str, object]:
    relative = path.relative_to(ROOT).as_posix()
    return {"bytes": path.stat().st_size, "classification": "public", "local_path": relative, "remote_path": f"terminal-bench/{ROOT.name}/{relative}", "sha256": sha256(path)}


def main() -> None:
    final_outputs = (COMBINED_VIDEO, THUMBNAIL, YOUTUBE_METADATA, RECEIPT, AMENDMENT, PUBLICATION)
    existing = [path for path in final_outputs if path.exists()]
    if existing:
        raise FileExistsError("v6 outputs already exist: " + ", ".join(path.name for path in existing))
    required = [FIGURES / "provenance.json", ASSETS / "geodi-dot.svg", ASSETS / "harbor-wordmark-dark.png", ASSETS / "terminalbench-icon-strip-transparent-v5.png"]
    if missing := [path for path in required if not path.is_file()]:
        raise FileNotFoundError(", ".join(path.as_posix() for path in missing))
    pages_by_language = {lang: build_pages(lang) for lang in ("ko", "en")}
    probes: dict[str, object] = {}
    for language, pages in pages_by_language.items():
        render_html(pages, HTMLS[language], language)
        probes[language] = V3.render_video(pages, HTMLS[language], VIDEOS[language])
    combined_probe = combine_videos()
    render_thumbnail()
    write_youtube(pages_by_language)
    generated_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    added = [HTMLS["ko"], HTMLS["en"], COMBINED_VIDEO, THUMBNAIL, YOUTUBE_METADATA, RECEIPT]
    receipt = {
        "schema_id": "geode.eval-evidence-video-receipt@6",
        "generated_at": generated_at,
        "score_authority": False,
        "presentation": {"sequence": "result -> heterogeneity -> contribution -> design -> authority -> accounting -> failures -> publication -> conclusion", "slides_per_language": len(pages_by_language["ko"]), "language_order": ["ko", "en"], "design": "paper-style figures on opaque white canvas; color restricted to data state; no decorative cards or colored borders"},
        "figure_provenance": {"path": "recording/figures-v6/provenance.json", "sha256": sha256(FIGURES / "provenance.json")},
        "language_variants": {lang: {"html": {"path": HTMLS[lang].relative_to(ROOT).as_posix(), "sha256": sha256(HTMLS[lang]), "bytes": HTMLS[lang].stat().st_size}, "video": {"path": VIDEOS[lang].relative_to(ROOT).as_posix(), "sha256": sha256(VIDEOS[lang]), "bytes": VIDEOS[lang].stat().st_size, "probe": probes[lang]}} for lang in ("ko", "en")},
        "combined_video": {"path": COMBINED_VIDEO.relative_to(ROOT).as_posix(), "sha256": sha256(COMBINED_VIDEO), "bytes": COMBINED_VIDEO.stat().st_size, "probe": combined_probe, "order": ["ko", "en"]},
        "thumbnail": {"path": THUMBNAIL.relative_to(ROOT).as_posix(), "sha256": sha256(THUMBNAIL), "bytes": THUMBNAIL.stat().st_size},
        "labels": {"canonical_time": "UTC", "display_time": "Asia/Seoul KST", "observer_capture": "procedure evidence only", "trajectory_reconstruction": "derived replay; not raw PTY evidence", "score_authority": "Harbor result and verifier receipt only"},
    }
    dump(RECEIPT, receipt)
    amendment = {
        "schema": "terminalbench21.publication-amendment-receipt.v1",
        "created_at": generated_at,
        "reason": "Add a result-first paper-style evidence film with reproducible quantitative figures, task-level heterogeneity, failure decomposition, and explicit measurement-system accomplishments; benchmark evidence and scores are unchanged.",
        "prior_artifact_commit": PRIOR_PUBLICATION_REVISION,
        "added_entries": [path.relative_to(ROOT).as_posix() for path in [*added, AMENDMENT, ROOT / "render-paper-figures-v6.py", ROOT / "render-evidence-video-v6.py", FIGURES / "figure-brief.md", FIGURES / "provenance.json"]],
        "evidence_boundaries": {"score_authority": "Harbor result and verifier receipts only", "figures_and_video": "derived presentation evidence only"},
        "verification": {"source_hashes_verified": True, "video_probe_passed": True, "full_video_decode_pending": True, "visual_sample_review_pending": True, "secret_scan_pending": True, "pii_scan_pending": True, "host_local_path_scan_pending": True},
    }
    dump(AMENDMENT, amendment)
    publication = json.loads((ROOT / "publication-v5.json").read_text(encoding="utf-8"))
    publication["artifact_repository"]["base_revision"] = PRIOR_PUBLICATION_REVISION
    publication["publication"] = {"artifact_merge_revision": None, "published_at": None, "status": "prepared"}
    publication["notes"]["video_v6"] = "additive result-first paper-style KO then EN evidence film; figures and video are derived evidence; scores unchanged"
    public_files = [HTMLS["ko"], HTMLS["en"], COMBINED_VIDEO, THUMBNAIL, YOUTUBE_METADATA, RECEIPT, AMENDMENT, ROOT / "render-paper-figures-v6.py", ROOT / "render-evidence-video-v6.py", FIGURES / "figure-brief.md", FIGURES / "provenance.json", *sorted(FIGURES.glob("*.png")), *sorted(FIGURES.glob("*.svg"))]
    known = {entry["remote_path"] for entry in publication["entries"]}
    new_entries = [publication_entry(path) for path in public_files]
    if known.intersection(entry["remote_path"] for entry in new_entries):
        raise RuntimeError("v6 publication would overwrite an existing remote path")
    publication["entries"].extend(new_entries)
    dump(PUBLICATION, publication)
    print(json.dumps({"slides_per_language": len(pages_by_language["ko"]), "combined_duration": combined_probe["format"]["duration"], "combined_sha256": sha256(COMBINED_VIDEO)}, sort_keys=True))


if __name__ == "__main__":
    main()
