# GPT-5.6 Luna / Terra / Sol effort-surface measurement

Date: 2026-08-11

GEODE runtime revision: `ef1199c25a30d6194b83b8783306dd44738e0bf8`

Authority: routing and backend-acceptance diagnostic only;
`promotion_authority=none`

## Scope and contract

The run measured all six effort values that GEODE exposes for the requested
GPT-5.6 targets, in Luna → Terra → Sol order:

`none`, `low`, `medium`, `high`, `xhigh`, `max`

Each model-effort pair used the same deterministic prompt and the production
route resolved by GEODE: provider `openai`, adapter `codex-oauth`, source
`subscription`. A passing row required all of the following:

1. requested effort equals the Responses wire value;
2. the backend accepts the request;
3. the response terminates normally without a tool call; and
4. visible text equals `EFFORT_OK` after trimming whitespace.

The probe appended every result before continuing and stopped on a failed
combination. Pre-response provider failures were retried only on the identical
model-effort pair, up to the AgenticLoop's five-attempt boundary. A prior pass
was skipped when resuming the same JSONL.

## Result

All **18/18 unique model-effort combinations passed**. Requested effort and
wire effort matched 18/18, and exact response text matched 18/18.

| Model | Passed | Median latency | Mean latency | Overload attempts |
|---|---:|---:|---:|---:|
| `gpt-5.6-luna` | 6/6 | 5.468s | 5.775s | 2 |
| `gpt-5.6-terra` | 6/6 | 4.378s | 8.139s | 4 |
| `gpt-5.6-sol` | 6/6 | 2.364s | 2.966s | 0 |

The 18 successful rows used 468 input tokens and 126 output tokens. Every
successful call reported 26 input and 7 output tokens, with zero cache reads
and zero provider-reported reasoning tokens.

The raw record contains 19 top-level rows: 18 final passes plus the first
`Luna/low` overload failure retained before the resumable retry behavior was
added. Nested retry histories retain five more overload attempts. In total,
24 provider attempts produced six transient overloads:

- `Luna/low`: two overloads before success across the stopped and resumed run;
- `Terra/none`: three overloads before success;
- `Terra/medium`: one overload before success.

No run switched model, adapter, provider, source, or effort to recover.

## Failure-driven improvements

Three preflight defects were corrected before the final sweep continued:

1. An initially guessed test filename did not exist; the owning tests were
   discovered from code references and the corrected targeted gate passed.
2. The first probe forced every provider onto subscription. GEODE actually
   resolves Anthropic `auto → payg` and OpenAI `auto → subscription`; the
   probe now uses the same `infer_source → resolve_for` production path.
3. The Codex SSE backend emitted overload as generic `openai.APIError`, which
   GEODE classified as `unknown`. The shared classifier now maps the narrow
   overload signature to `server`, with a regression test.

The Anthropic overscope preflight was excluded from this GPT-5.6 artifact:
the local PAYG route has insufficient credit and the local Claude Code
organization disables subscription access. Neither failure is evidence about
GPT-5.6 or its effort surface.

## Interpretation limits

This is an interface and transport measurement, not an intelligence or safety
evaluation. The prompt is intentionally trivial, there is one successful
sample per pair, and latency was measured sequentially under changing provider
load. Therefore latency is not expected to be monotonic with effort, and the
zero reasoning-token count does not show that higher effort has no effect.

OpenAI's current [model pages](https://developers.openai.com/api/docs/models)
expose the GPT-5.6 family, while the
[Codex model guide](https://developers.openai.com/codex/models) distinguishes
`Max` reasoning on one task from `Ultra`, which adds automatic task
delegation. GEODE correctly treats `Ultra` as orchestration, not as a
Responses `reasoning.effort` wire value.

## Artifacts

- Machine summary:
  [`2026-08-11-gpt56-luna-terra-sol-effort-surface.json`](2026-08-11-gpt56-luna-terra-sol-effort-surface.json)
- Append-only attempt record:
  [`2026-08-11-gpt56-luna-terra-sol-effort-surface.jsonl`](2026-08-11-gpt56-luna-terra-sol-effort-surface.jsonl)
- JSONL SHA-256:
  `7abcfb5d7e6899363f1c975a94ac16a622189d53fb59e40b4fc8f7e5b2ec9de9`

The public scan found no credentials, bearer tokens, local home paths, email
addresses, or provider reasoning bodies.
