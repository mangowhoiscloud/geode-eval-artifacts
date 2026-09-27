#!/usr/bin/env python3
"""Freeze step 5 (05 v2.2 §3.7-1, run-packets README): check Jev selector tolerances, no model.

Before U4, U5s or X2 starts, confirm that the Jev Score selector receives the
frozen bounds as explicit arguments: ``sum_tolerance=0.025`` and the frozen
``score_tolerance`` from ``score-tolerance-freeze.json``. The code defaults are the
strict 1e-5 for both, so a forgotten argument silently applies the strict bound.

Usage (run with the pinned checkout's interpreter; nothing leaves the process):

  <checkout>/.venv/bin/python check_selector_tolerances.py \
      --source <pinned checkout> --freeze <run>/score-tolerance-freeze.json \
      [--pools <pools.jsonl> [--states <states.jsonl>]] \
      [--records <dispatch-records.jsonl> ...] \
      [--selectors MODULE:FUNCTION]

Checks (exit 0 only if every check passes):
  F  the freeze file: score_tolerance in [0.03, 0.05] (the §4.1 rule range),
     sum_tolerance 0.025, and when ``u0b_max_abs_deviation`` (or
     ``score_expectation.max_abs_deviation``) is present, score_tolerance equals
     ``score_selection.score_expectation_tolerance`` of it.
  S  a Jev ``PointwiseSelector`` built with the frozen values reports exactly those
     ``tolerances``; with ``--pools`` every pool x order adapter is constructed
     (preflight) and carries the same bounds. ``--selectors`` imports the run
     driver's selector factory (a zero-argument callable returning the selectors
     it will pass to ``dispatch_selection``) and checks every Jev selector in it.
  P  behaviour, offline through the real judge boundary (MockTransport TypeSafe):
     a Score answer off its expectation by d, 1e-5 < d < frozen, is admitted by
     the explicit selector and rejected by a default-constructed one; an answer
     off by frozen + 0.005 is rejected by the explicit selector.
  R  with ``--records``: every Jev pointwise entry of every dispatch record has
     ``tolerances`` equal to the freeze and every receipt records the same
     ``sum_tolerance`` / ``score_tolerance``.
  U  with ``--u0b-records`` (U0b dispatch records): the §4.1 rule recomputed in
     exact decimal from each Jev receipt's raw answer must equal the frozen
     score_tolerance. The code's float path (``score_expectation.tolerance``) can
     round an exact 0.03/0.04 maximum up one 0.01 step (binary noise before the
     ceiling); the exact value is reported beside it.
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
import json
import math
import socket
import sys
from pathlib import Path
from typing import Any

SUM_TOLERANCE = 0.025


def _deny_network() -> None:
    real_connect = socket.socket.connect

    def connect(self: socket.socket, address: Any) -> Any:
        if self.family in (socket.AF_INET, socket.AF_INET6):
            raise RuntimeError("check_selector_tolerances: network access is disabled")
        return real_connect(self, address)

    socket.socket.connect = connect  # type: ignore[method-assign]


def _freeze_values(document: dict[str, Any]) -> tuple[float, float, float | None]:
    score = document.get("score_tolerance", document.get("tolerance"))
    expectation = document.get("score_expectation")
    if score is None and isinstance(expectation, dict):
        score = expectation.get("tolerance")
    observed = document.get("u0b_max_abs_deviation")
    if observed is None and isinstance(expectation, dict):
        observed = expectation.get("max_abs_deviation")
    sum_tolerance = document.get("sum_tolerance", SUM_TOLERANCE)
    if isinstance(score, bool) or not isinstance(score, (int, float)):
        raise ValueError("freeze file has no numeric score_tolerance")
    return float(sum_tolerance), float(score), None if observed is None else float(observed)


def exact_u0b_rule(paths: list[Path]) -> dict[str, Any]:
    """Max |score - Σ level·p| over Jev Score receipts, in exact decimal, and the §4.1 rule."""
    from decimal import ROUND_CEILING, Decimal

    deviations: list[Decimal] = []
    float_max = 0.0
    for path in paths:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            for entry in record["selectors"].values():
                if entry.get("engine") != "jev" or entry.get("type") != "pointwise":
                    continue
                for result in entry["orders"].values():
                    receipt = result.get("receipt") or {}
                    raw = receipt.get("raw_answer")
                    if not isinstance(raw, str):
                        continue
                    try:
                        answers = json.loads(raw, parse_float=Decimal)
                    except ValueError:
                        continue
                    for answer in answers.values() if isinstance(answers, dict) else ():
                        score = answer.get("score") if isinstance(answer, dict) else None
                        probabilities = answer.get("probabilities") if isinstance(answer, dict) else None
                        if isinstance(score, bool) or not isinstance(score, (int, Decimal)) or not isinstance(probabilities, dict):
                            continue
                        try:
                            expected = sum((Decimal(int(level)) * Decimal(p) for level, p in probabilities.items()), Decimal(0))
                        except (TypeError, ValueError, ArithmeticError):
                            continue
                        deviations.append(abs(Decimal(score) - expected))
                    if isinstance(result.get("expectation_deviation"), (int, float)):
                        float_max = max(float_max, float(result["expectation_deviation"]))
    if not deviations:
        return {"orders_measured": 0, "exact_max": None, "exact_rule": None, "float_max": None}
    observed = max(deviations)
    ceiling = observed.quantize(Decimal("0.01"), rounding=ROUND_CEILING)
    rule = min(Decimal("0.05"), max(Decimal("0.03"), ceiling))
    return {"orders_measured": len(deviations), "exact_max": str(observed), "exact_rule": float(rule), "float_max": float_max}


def _score_answer(level_mix: float, deviation: float, legend: list[str]) -> dict[str, Any]:
    """A Jev Score answer whose score is off its expectation by exactly ``deviation``."""
    probabilities = {str(level): 0.0 for level in range(len(legend))}
    lower = math.floor(level_mix)
    probabilities[str(lower)] = 1.0 - (level_mix - lower)
    if lower + 1 < len(legend):
        probabilities[str(lower + 1)] += level_mix - lower
    expected = sum(int(k) * v for k, v in probabilities.items())
    return {
        "type": "score",
        "score": expected + deviation,
        "legend": {str(level): text for level, text in enumerate(legend)},
        "probabilities": probabilities,
        "confidence": 0.5,
    }


async def _probe(ss: Any, freeze_sum: float, freeze_score: float) -> dict[str, Any]:
    """Run the real judge boundary offline for explicit and default Jev selectors."""
    from unittest import mock

    import httpx
    from core.agent import candidate_sampling
    from core.config import settings
    from core.llm.adapters.typesafe import JEV_MODEL, SystemOneAdapter
    from pydantic import SecretStr

    from evals.benchmarks.decision_candidate import CANDIDATE_LEVELS

    pool = ss.FrozenPool(
        "tolerance-probe",
        "Tolerance probe task: pick the candidate that fulfils the request.",
        (
            ss.PoolCandidate("probe-a", "Candidate A: complete answer with evidence.", 3),
            ss.PoolCandidate("probe-b", "Candidate B: partial answer.", 1),
        ),
    )
    deviation = {"value": 0.0}

    def transport(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        answers = {
            key: _score_answer(2.5 if index == 0 else 1.25, deviation["value"], list(CANDIDATE_LEVELS))
            for index, key in enumerate(body["state"]["candidates"])
        }
        return httpx.Response(
            200,
            json={"model": JEV_MODEL, "usage": {"input_tokens": 50, "output_tokens": 0}, "answers": answers},
            headers={"x-typesafe-request-id": "tolerance-probe"},
        )

    class _Unused:
        name, provider, source = "unused-subscription", "openai", "subscription"
        billing_type = ss.AdapterBillingType.SUBSCRIPTION

        async def acomplete(self, request: Any) -> Any:  # pragma: no cover - never reached
            raise AssertionError("the Jev selector must not reach the Astra route")

    results: dict[str, Any] = {}
    previous = settings.llm_max_retries
    settings.llm_max_retries = 1
    try:
        async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
            backend = SystemOneAdapter("typesafe", SecretStr("tolerance-probe-offline"), client=client)
            explicit = ss.PointwiseSelector(
                "jev-explicit", "jev", backend, sum_tolerance=freeze_sum, score_tolerance=freeze_score
            )
            default = ss.PointwiseSelector("jev-default", "jev", backend)
            with mock.patch.object(candidate_sampling, "resolve_for", lambda *_args: _Unused()):
                for label, value in (
                    ("inside", (freeze_score + 1e-5) / 2),
                    ("above", freeze_score + 0.005),
                ):
                    deviation["value"] = value
                    records = await ss.dispatch_selection([pool], [explicit, default])
                    entry = records[0]["selectors"]
                    results[label] = {
                        "deviation": value,
                        "explicit_valid": all(o["valid"] for o in entry["jev-explicit"]["orders"].values()),
                        "default_valid": all(o["valid"] for o in entry["jev-default"]["orders"].values()),
                        "explicit_strict_admitted": [
                            (o["receipt"] or {}).get("strict_admitted") for o in entry["jev-explicit"]["orders"].values()
                        ],
                        "explicit_tolerances": entry["jev-explicit"]["tolerances"],
                        "default_tolerances": entry["jev-default"]["tolerances"],
                    }
    finally:
        settings.llm_max_retries = previous
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", type=Path, required=True, help="pinned GEODE checkout")
    parser.add_argument("--freeze", type=Path, required=True, help="score-tolerance-freeze.json")
    parser.add_argument("--pools", type=Path)
    parser.add_argument("--states", type=Path)
    parser.add_argument("--records", type=Path, action="append", default=[])
    parser.add_argument("--u0b-records", type=Path, action="append", default=[],
                        help="U0b dispatch records; the exact decimal §4.1 rule must equal the freeze")
    parser.add_argument("--selectors", help="MODULE:FUNCTION returning the run's selectors")
    args = parser.parse_args(argv)
    _deny_network()
    source = str(args.source.resolve())
    while source in sys.path:
        sys.path.remove(source)
    sys.path.insert(0, source)
    from evals.benchmarks import score_selection as ss

    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, **detail: Any) -> None:
        checks.append({"name": name, "passed": bool(passed), **detail})

    document = json.loads(args.freeze.read_text(encoding="utf-8"))
    freeze_sum, freeze_score, observed = _freeze_values(document)
    rule = None if observed is None else ss.score_expectation_tolerance(observed)
    check(
        "F freeze values: sum 0.025, score in [0.03, 0.05], equal to the §4.1 rule when U0b max is recorded",
        freeze_sum == SUM_TOLERANCE
        and 0.03 <= freeze_score <= 0.05
        and (rule is None or math.isclose(rule, freeze_score, abs_tol=0)),
        sum_tolerance=freeze_sum,
        score_tolerance=freeze_score,
        u0b_max_abs_deviation=observed,
        rule_value=rule,
    )
    from core.llm.adapters.typesafe import SystemOneAdapter
    from pydantic import SecretStr

    backend = SystemOneAdapter("typesafe", SecretStr("tolerance-check-offline"))
    selector = ss.PointwiseSelector(
        "jev-pointwise", "jev", backend, sum_tolerance=freeze_sum, score_tolerance=freeze_score
    )
    expected = {"sum_tolerance": freeze_sum, "score_tolerance": freeze_score}
    check("S1 reference Jev selector reports the frozen tolerances", selector.tolerances == expected, tolerances=selector.tolerances)
    if args.pools:
        pools = ss.load_pools(args.pools, states_path=args.states)
        bounds = set()
        for pool in pools:
            for order in ss.ORDERS:
                adapter = selector.matched_adapter(pool, order, [])
                bounds.add((adapter._sum_tolerance, adapter._score_tolerance))
        check(
            "S2 every pool x order adapter is constructed with the frozen bounds",
            bounds == {(freeze_sum, freeze_score)},
            pools=len(pools),
            bounds=sorted(bounds),
        )
    if args.selectors:
        module_name, _, function = args.selectors.partition(":")
        factory = getattr(importlib.import_module(module_name), function)
        selectors = list(factory())
        jev = [s for s in selectors if getattr(s, "engine", None) == "jev"]
        check(
            "S3 every Jev selector from the run driver's factory carries the frozen tolerances",
            bool(jev) and all(s.tolerances == expected for s in jev),
            selectors={s.name: s.tolerances for s in selectors},
        )
    probe = asyncio.run(_probe(ss, freeze_sum, freeze_score))
    check(
        "P1 inside the frozen bound: explicit selector admits, default (strict 1e-5) rejects",
        probe["inside"]["explicit_valid"]
        and not probe["inside"]["default_valid"]
        and probe["inside"]["explicit_tolerances"] == expected
        and probe["inside"]["default_tolerances"]
        == {"sum_tolerance": 1e-05, "score_tolerance": 1e-05}
        and probe["inside"]["explicit_strict_admitted"] == [False, False],
        probe=probe["inside"],
    )
    check(
        "P2 above the frozen bound: the explicit selector rejects",
        not probe["above"]["explicit_valid"],
        probe=probe["above"],
    )
    for path in args.records:
        mismatches: list[str] = []
        entries = 0
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            for name, entry in record["selectors"].items():
                if entry.get("engine") != "jev" or entry.get("type") != "pointwise":
                    continue
                entries += 1
                if entry.get("tolerances") != expected:
                    mismatches.append(f"{path.name}:{number}:{name}:tolerances={entry.get('tolerances')}")
                for order, result in entry["orders"].items():
                    receipt = result.get("receipt") or {}
                    got = {k: receipt.get(k) for k in ("sum_tolerance", "score_tolerance")}
                    if receipt and got != expected:
                        mismatches.append(f"{path.name}:{number}:{name}:{order}:receipt={got}")
        check(
            f"R records {path.name}: every Jev pointwise entry and receipt uses the frozen tolerances",
            entries > 0 and not mismatches,
            jev_entries=entries,
            mismatches=mismatches[:5],
        )
    if args.u0b_records:
        exact = exact_u0b_rule(args.u0b_records)
        float_rule = None if exact["float_max"] is None else ss.score_expectation_tolerance(exact["float_max"])
        check(
            "U the frozen score_tolerance equals the §4.1 rule recomputed in exact decimal from U0b raw answers",
            exact["exact_rule"] is not None and math.isclose(exact["exact_rule"], freeze_score, abs_tol=0),
            **exact,
            float_path_rule=float_rule,
        )
    passed = all(row["passed"] for row in checks)
    print(json.dumps({"passed": passed, "model_dispatches": 0, "checks": checks}, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
