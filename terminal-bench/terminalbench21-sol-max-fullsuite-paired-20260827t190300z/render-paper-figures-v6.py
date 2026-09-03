#!/usr/bin/env python3
"""Render paper-style v6 figures from canonical Terminal-Bench summaries."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "recording" / "figures-v6"
RESULTS = ROOT / "native-results.json"
OUTCOMES = ROOT / "outcomes.json"
ATTEMPTS = ROOT / "attempts.jsonl"
SEED = 20260904
RESAMPLES = 20_000

INK = "#171717"
MID = "#777777"
LIGHT = "#D9D9D5"
GEODE = "#137A3A"
CODEX = "#285A84"
RUST = "#A84A3A"
PAPER = "#FFFFFF"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load() -> tuple[dict[str, object], dict[str, object]]:
    return (
        json.loads(RESULTS.read_text(encoding="utf-8")),
        json.loads(OUTCOMES.read_text(encoding="utf-8")),
    )


def setup() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Apple SD Gothic Neo", "Arial", "DejaVu Sans"],
            "axes.edgecolor": INK,
            "axes.labelcolor": INK,
            "axes.titlecolor": INK,
            "axes.titlesize": 18,
            "axes.titleweight": 600,
            "axes.labelsize": 13,
            "xtick.color": INK,
            "ytick.color": INK,
            "xtick.labelsize": 11,
            "ytick.labelsize": 11,
            "figure.facecolor": PAPER,
            "axes.facecolor": PAPER,
            "savefig.facecolor": PAPER,
            "savefig.transparent": False,
            "axes.unicode_minus": False,
        }
    )


def finish(
    fig: plt.Figure,
    name: str,
    *,
    left: float = 0.09,
    right: float = 0.97,
    top: float = 0.86,
    bottom: float = 0.18,
    wspace: float | None = None,
) -> list[Path]:
    fig.subplots_adjust(left=left, right=right, top=top, bottom=bottom, wspace=wspace)
    paths = [OUT / f"{name}.png", OUT / f"{name}.svg"]
    fig.savefig(paths[0], dpi=150, facecolor=PAPER)
    fig.savefig(paths[1], facecolor=PAPER)
    plt.close(fig)
    return paths


def clean_axes(ax: plt.Axes, *, grid: str | None = "x") -> None:
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    if grid:
        ax.grid(axis=grid, color="#ECECEA", linewidth=1, zorder=0)
    ax.set_axisbelow(True)


def measurement_cascade(lang: str) -> list[Path]:
    ko = lang == "ko"
    stages = ["의도한 셀", "실행된 셀", "유효 셀", "통과 셀"] if ko else ["Intended", "Executed", "Valid", "Passed"]
    values = [890, 870, 864, 675]
    fig, ax = plt.subplots(figsize=(12.8, 5.333))
    x = np.arange(len(stages))
    ax.plot(x, values, color=INK, linewidth=2.2, zorder=2)
    ax.scatter(x, values, s=115, facecolor=PAPER, edgecolor=INK, linewidth=2.3, zorder=3)
    for px, py in zip(x, values):
        ax.text(px, py + 31, f"{py}", ha="center", fontsize=18, fontweight=650, color=INK)
    branches = [
        (0.5, 880, 20, "사전 대칭 제외" if ko else "prospective symmetric exclusions", RUST),
        (1.5, 844, 6, "미해소 인프라 무효" if ko else "unresolved infrastructure-invalid", RUST),
        (2.5, 710, 189, "프로토콜 유효 0점" if ko else "protocol-valid zeroes", MID),
    ]
    for px, py, count, label, color in branches:
        ax.annotate(
            f"-{count}  {label}",
            xy=(px, py),
            xytext=(0, -42),
            textcoords="offset points",
            ha="center",
            fontsize=12,
            color=color,
            arrowprops={"arrowstyle": "-", "color": color, "lw": 1.3},
        )
    ax.set_xticks(x, stages)
    ax.set_ylim(0, 980)
    ax.set_ylabel("셀 수" if ko else "Cells")
    ax.set_title("분모를 바꾸지 않고 상태를 분리했습니다" if ko else "Each state is separated without silently changing the denominator", loc="left", pad=18)
    ax.text(0, -0.22, "Source: native-results.json + outcomes.json · derived view · score authority: Harbor verifier receipts" if not ko else "출처: native-results.json + outcomes.json · 파생 도표 · 점수 권한: Harbor verifier receipt", transform=ax.transAxes, fontsize=9.5, color=MID)
    clean_axes(ax, grid="y")
    return finish(fig, f"measurement-cascade-{lang}")


def pass_rate_comparison(lang: str) -> list[Path]:
    ko = lang == "ko"
    rows = [
        ("공통 429셀 · GEODE" if ko else "429 exact-common · GEODE", 339, 429, GEODE, "o"),
        ("공통 429셀 · Codex" if ko else "429 exact-common · Codex", 331, 429, CODEX, "s"),
        ("보조 범위 · GEODE" if ko else "Secondary coverage · GEODE", 344, 435, GEODE, "o"),
        ("보조 범위 · Codex" if ko else "Secondary coverage · Codex", 331, 429, CODEX, "s"),
    ]
    fig, ax = plt.subplots(figsize=(12.8, 5.333))
    y = np.arange(len(rows))[::-1]
    for py, (label, num, den, color, marker) in zip(y, rows):
        rate = num / den * 100
        ax.hlines(py, 0, rate, color=LIGHT, linewidth=2, zorder=1)
        ax.scatter(rate, py, s=150, marker=marker, facecolor=color, edgecolor=INK, linewidth=0.8, zorder=3)
        ax.text(rate + 0.8, py, f"{rate:.2f}%  ({num}/{den})", va="center", fontsize=13, color=INK)
    ax.set_yticks(y, [row[0] for row in rows])
    ax.set_xlim(0, 100)
    ax.set_xlabel("Verifier 통과율 (%)" if ko else "Verifier pass rate (%)")
    ax.set_title("동일한 429셀에서 GEODE가 8개 더 통과했습니다" if ko else "GEODE passed eight more of the same 429 cells", loc="left", pad=18)
    ax.text(0.99, 1.015, "+1.86 percentage points · exact-common only", transform=ax.transAxes, ha="right", fontsize=12, color=GEODE)
    ax.text(0, -0.22, "두 보조 수치의 분모는 다릅니다. 직접 비교는 exact-common 행에서만 성립합니다." if ko else "Secondary denominators differ. Direct comparison is valid only for the exact-common rows.", transform=ax.transAxes, fontsize=10, color=MID)
    clean_axes(ax)
    return finish(fig, f"pass-rate-comparison-{lang}", left=0.22, bottom=0.2)


def paired_outcomes(lang: str) -> list[Path]:
    ko = lang == "ko"
    labels = ["둘 다 통과", "GEODE만 통과", "Codex만 통과", "둘 다 실패"] if ko else ["Both pass", "GEODE only", "Codex only", "Both fail"]
    values = [286, 53, 45, 45]
    colors = [INK, GEODE, CODEX, MID]
    fig, ax = plt.subplots(figsize=(12.8, 5.333))
    bars = ax.bar(labels, values, color=colors, width=0.58, zorder=2)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 8, str(value), ha="center", fontsize=18, fontweight=650)
    ax.set_ylim(0, 330)
    ax.set_ylabel("공통 셀 수" if ko else "Exact-common cells")
    ax.set_title("순효과는 GEODE-only 53개에서 Codex-only 45개를 뺀 +8셀입니다" if ko else "The net edge is 53 GEODE-only minus 45 Codex-only cells", loc="left", pad=18)
    ax.text(0, -0.22, "n=429 paired cells · each bar starts at zero" if not ko else "n=429 paired cells · 모든 막대는 0에서 시작합니다", transform=ax.transAxes, fontsize=10, color=MID)
    clean_axes(ax, grid="y")
    return finish(fig, f"paired-outcomes-{lang}")


def task_rows() -> list[dict[str, object]]:
    cells: dict[tuple[str, str, int], int] = {}
    for line in ATTEMPTS.read_text(encoding="utf-8").splitlines():
        attempt = json.loads(line)
        surface = attempt.get("change", {}).get("surface", "")
        arm_task = re.fullmatch(r"(geode|native):terminal-bench/(.+)", surface)
        repetition = re.search(r"repetition[- ](\d+)", attempt.get("change", {}).get("description", ""))
        if not arm_task or not repetition:
            continue
        if not attempt.get("selected_for_analysis") or attempt.get("validity") != "valid":
            continue
        cells[(arm_task.group(1), arm_task.group(2), int(repetition.group(1)))] = int(attempt.get("outcome") == "passed")
    rows: list[dict[str, object]] = []
    for task in sorted({key[1] for key in cells}):
        repetitions = [index for index in range(1, 6) if ("geode", task, index) in cells and ("native", task, index) in cells]
        if not repetitions:
            continue
        geode_passes = sum(cells[("geode", task, index)] for index in repetitions)
        native_passes = sum(cells[("native", task, index)] for index in repetitions)
        rows.append(
            {
                "name": task,
                "common": len(repetitions),
                "geode": geode_passes,
                "native": native_passes,
                "delta": (geode_passes - native_passes) / len(repetitions) * 100,
            }
        )
    assert sum(int(row["common"]) for row in rows) == 429
    assert sum(int(row["geode"]) for row in rows) == 339
    assert sum(int(row["native"]) for row in rows) == 331
    return rows


def bootstrap(rows: list[dict[str, object]]) -> tuple[float, float, float]:
    values = np.array([float(row["delta"]) for row in rows])
    rng = np.random.default_rng(SEED)
    samples = values[rng.integers(0, len(values), size=(RESAMPLES, len(values)))].mean(axis=1)
    low, high = np.percentile(samples, [2.5, 97.5])
    return float(values.mean()), float(low), float(high)


def task_heterogeneity(lang: str) -> tuple[list[Path], dict[str, object]]:
    ko = lang == "ko"
    source_rows = task_rows()
    mean, low, high = bootstrap(source_rows)
    rows = sorted(source_rows, key=lambda row: (float(row["delta"]), str(row["name"])))
    deltas = np.array([float(row["delta"]) for row in rows])
    positive = int((deltas > 0).sum())
    tie = int((deltas == 0).sum())
    negative = int((deltas < 0).sum())
    fig, (ax, ci) = plt.subplots(1, 2, figsize=(12.8, 5.333), gridspec_kw={"width_ratios": [3.4, 1.1], "wspace": 0.16})
    y = np.arange(len(rows))
    colors = np.where(deltas > 0, GEODE, np.where(deltas < 0, CODEX, MID))
    nonzero = deltas != 0
    ax.scatter(deltas[nonzero], y[nonzero], c=colors[nonzero], marker="o", s=34, linewidths=0.5, edgecolors=INK, zorder=3)
    ax.scatter(deltas[~nonzero], y[~nonzero], c=colors[~nonzero], marker="|", s=85, linewidths=1.0, zorder=3)
    ax.axvline(0, color=INK, linewidth=1.2)
    ax.set_xlim(-110, 110)
    ax.set_ylim(-3, len(rows) + 2)
    ax.set_yticks([])
    ax.set_xlabel("태스크별 통과율 차이 · GEODE - Codex (pp)" if ko else "Task-level pass-rate delta · GEODE - Codex (pp)")
    ax.set_title("우세 태스크 수는 16 대 16으로 대칭입니다" if ko else "The number of task wins is symmetric: 16 versus 16", loc="left", pad=18)
    ax.text(0.01, 0.98, f"Codex 우세 {negative}" if ko else f"Codex-positive {negative}", transform=ax.transAxes, va="top", color=CODEX, fontsize=12)
    ax.text(0.50, 0.98, f"동률 {tie}" if ko else f"Ties {tie}", transform=ax.transAxes, ha="center", va="top", color=MID, fontsize=12)
    ax.text(0.99, 0.98, f"GEODE 우세 {positive}" if ko else f"GEODE-positive {positive}", transform=ax.transAxes, ha="right", va="top", color=GEODE, fontsize=12)
    clean_axes(ax)
    ci.axvline(0, color=INK, linewidth=1.2)
    ci.errorbar(mean, 0, xerr=np.array([[mean - low], [high - mean]]), fmt="o", color=GEODE, ecolor=INK, capsize=6, markersize=8)
    ci.set_xlim(-12, 12)
    ci.set_ylim(-1, 1)
    ci.set_yticks([])
    ci.set_xlabel("차이 (pp)" if ko else "Delta (pp)")
    ci.set_title("태스크 클러스터\n부트스트랩" if ko else "Task-cluster\nbootstrap", loc="left", pad=18)
    ci.text(0.02, 0.53, "태스크 균형 평균" if ko else "Task-balanced mean", transform=ci.transAxes, fontsize=10, color=INK)
    ci.text(mean, 0.38, f"{mean:+.2f} pp", ha="center", fontsize=13, fontweight=650)
    ci.text(0, -0.48, f"95%: [{low:+.2f}, {high:+.2f}]", ha="center", fontsize=10, color=MID)
    clean_axes(ci)
    fig.text(0.09, 0.045, f"n={len(rows)} tasks · seed={SEED} · {RESAMPLES:,} resamples · task is the resampling unit", fontsize=9.5, color=MID)
    paths = finish(fig, f"task-heterogeneity-{lang}", left=0.08, top=0.80, bottom=0.21, wspace=0.24)
    return paths, {"tasks": len(rows), "geode_positive": positive, "ties": tie, "native_positive": negative, "task_balanced_mean_pp": mean, "bootstrap_percentile_95_pp": [low, high]}


def task_extremes(lang: str) -> list[Path]:
    ko = lang == "ko"
    rows = sorted(task_rows(), key=lambda row: (float(row["delta"]), str(row["name"])))
    selected = rows[:6] + rows[-6:]
    y = np.arange(len(selected))
    values = np.array([float(row["delta"]) for row in selected])
    colors = np.where(values > 0, GEODE, CODEX)
    fig, ax = plt.subplots(figsize=(12.8, 5.333))
    ax.axvline(0, color=INK, linewidth=1.2, zorder=1)
    ax.hlines(y, 0, values, color=LIGHT, linewidth=2, zorder=1)
    ax.scatter(values, y, c=colors, s=80, edgecolor=INK, linewidth=0.6, zorder=3)
    ax.set_yticks(y, [str(row["name"]) for row in selected])
    ax.set_xlim(-115, 115)
    ax.set_xlabel("공통 셀 통과율 차이 · GEODE - Codex (pp)" if ko else "Exact-common task pass-rate delta · GEODE - Codex (pp)")
    ax.set_title("평균 차이는 소수의 큰 태스크별 역전에서 나옵니다" if ko else "The mean difference comes from a few large task-level reversals", loc="left", pad=18)
    for py, value, row in zip(y, values, selected):
        label = f"{value:+.0f} pp  ({row['geode']}-{row['native']} / {row['common']})"
        ax.text(value + (-3 if value > 0 else 3), py, label, ha="right" if value > 0 else "left", va="center", fontsize=10.5, color=INK)
    ax.text(0.01, 1.02, "Codex 우세" if ko else "Codex-positive", transform=ax.transAxes, color=CODEX, fontsize=11)
    ax.text(0.99, 1.02, "GEODE 우세" if ko else "GEODE-positive", transform=ax.transAxes, ha="right", color=GEODE, fontsize=11)
    clean_axes(ax)
    return finish(fig, f"task-extremes-{lang}", left=0.22, top=0.84, bottom=0.18)


def failure_decomposition(outcomes: dict[str, object], lang: str) -> list[Path]:
    ko = lang == "ko"
    classes = outcomes["failure_classes"]
    selected = [
        ("Verifier 0점" if ko else "Verifier reward zero", int(classes["verifier-reward-zero"])),
        ("Agent timeout" if ko else "Canonical agent timeout", int(classes["canonical-agent-timeout"])),
        ("모델 안전 거절" if ko else "Model safety refusal", int(classes["model-safety-refusal"])),
    ]
    invalid = [
        ("설치 timeout" if ko else "Agent setup timeout", int(classes["infrastructure-exception:AgentSetupTimeoutError"])),
        ("Agent 비정상 종료" if ko else "Non-zero agent exit", int(classes["infrastructure-exception:NonZeroAgentExitCodeError"])),
        ("Receipt 판정" if ko else "Receipt-classified", int(classes["infrastructure-exception:receipt-classified"])),
        ("인증 미주입" if ko else "Auth not injected", int(classes["operator-protocol-misconfiguration:subscription-auth-not-injected"])),
        ("Provider 과부하" if ko else "Provider overload", int(classes["infrastructure-exception:ApiOverloadedError"])),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 5.333), gridspec_kw={"wspace": 0.42})
    for ax, rows, color, title, xlabel in [
        (axes[0], selected, INK, "선택된 유효 0점 · n=189" if ko else "Selected valid zeroes · n=189", "선택 셀" if ko else "Selected cells"),
        (axes[1], invalid, RUST, "인프라 무효 시도 · n=72" if ko else "Infrastructure-invalid attempts · n=72", "모델 시도" if ko else "Model attempts"),
    ]:
        labels = [row[0] for row in rows][::-1]
        values = [row[1] for row in rows][::-1]
        bars = ax.barh(labels, values, color=color, height=0.55, zorder=2)
        for bar, value in zip(bars, values):
            ax.text(value + max(values) * 0.03, bar.get_y() + bar.get_height() / 2, str(value), va="center", fontsize=12)
        ax.set_xlim(0, max(values) * 1.23)
        ax.set_xlabel(xlabel)
        ax.set_title(title, loc="left", pad=16)
        clean_axes(ax)
    fig.suptitle("0점과 인프라 무효는 서로 다른 모집단입니다" if ko else "A valid zero and an infrastructure-invalid attempt are different populations", x=0.09, y=0.98, ha="left", fontsize=18, fontweight=600)
    fig.text(0.09, 0.045, "The left panel affects score; the right panel records replacement lineage. Only six native cells remained unresolved." if not ko else "왼쪽은 점수에 반영됩니다. 오른쪽은 보충 실행 계보를 기록하며, 최종 미해소 native 셀은 6개입니다.", fontsize=9.5, color=MID)
    return finish(fig, f"failure-decomposition-{lang}", left=0.18, top=0.76, bottom=0.19, wspace=0.5)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    setup()
    results, outcomes = load()
    exact = results["exact_common_cell_comparison"]
    assert exact == {"cells": 429, "geode_passes": 339, "native_passes": 331, "both_pass": 286, "geode_only": 53, "native_only": 45, "both_fail": 45}
    assert results["attempt_counts"] == {"model_attempt_rows": 936, "valid": 864, "invalid": 72, "supplements": 76}
    assert len(results["excluded_tasks"]) == 2 and sum(item["cells_per_arm"] for item in results["excluded_tasks"]) == 10
    assert len(results["unresolved_cells"]) == 6
    generated: list[Path] = []
    stats: dict[str, object] | None = None
    for lang in ("ko", "en"):
        generated.extend(measurement_cascade(lang))
        generated.extend(pass_rate_comparison(lang))
        generated.extend(paired_outcomes(lang))
        paths, lang_stats = task_heterogeneity(lang)
        generated.extend(paths)
        stats = lang_stats
        generated.extend(task_extremes(lang))
        generated.extend(failure_decomposition(outcomes, lang))
    assert stats is not None
    expected = {"tasks": 87, "geode_positive": 16, "ties": 55, "native_positive": 16}
    assert all(stats[key] == value for key, value in expected.items())
    assert abs(float(stats["task_balanced_mean_pp"]) - 1.264367816091954) < 1e-12
    low, high = stats["bootstrap_percentile_95_pp"]
    assert abs(low - -5.402298850574713) < 1e-9
    assert abs(high - 8.045977011494253) < 1e-9
    provenance = {
        "schema": "terminalbench21.figure-provenance.v1",
        "score_authority": False,
        "source_files": {
            "native-results.json": sha256(RESULTS),
            "outcomes.json": sha256(OUTCOMES),
            "attempts.jsonl": sha256(ATTEMPTS),
        },
        "canonical_assertions": {
            "intended_cells": 890,
            "executed_selected_cells": 870,
            "valid_selected_cells": 864,
            "passes": 675,
            "exact_common": exact,
            "attempt_counts": results["attempt_counts"],
        },
        "task_cluster_bootstrap": {"seed": SEED, "resamples": RESAMPLES, **stats},
        "figures": {path.name: {"bytes": path.stat().st_size, "sha256": sha256(path)} for path in generated},
        "transformation_script": {"path": Path(__file__).name, "sha256": sha256(Path(__file__))},
    }
    provenance_path = OUT / "provenance.json"
    provenance_path.write_text(json.dumps(provenance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"figures": len(generated), "stats": stats, "provenance_sha256": sha256(provenance_path)}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
