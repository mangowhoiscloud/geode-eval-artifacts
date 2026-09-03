# Terminal-Bench 2.1 evidence video instruction / 증거 영상 제작 지침

## 1. Why this exists / 왜 수행하는가

Research question:

> Under one frozen Terminal-Bench 2.1 task, model, budget, and verifier contract,
> how do GEODE and the native Codex harness differ in valid task completion and
> failure shape?

연구 질문은 “어느 모델이 더 좋은가”가 아니다. 같은 `gpt-5.6-sol` 모델을
두 agent harness에서 실행했을 때, prompt·tool·context·recovery·trace를
조정하는 실행 계층이 결과와 실패 형태에 어떤 차이를 만드는지 관찰한다.
이를 위해 task와 repetition이 같은 셀을 짝지어 비교하고, 원시 시도와
보충 시도를 삭제하지 않으며, 점수는 canonical verifier에만 맡긴다.

The study does not claim that the observed difference is a model-quality delta,
an official Terminal-Bench rank, or a timeless causal harness effect. The frozen
primary requires every planned cell to resolve under the declared protocol. Two
symmetrically excluded tasks and six unresolved native infrastructure-invalid
cells make that primary not measurable, so only explicitly denominated secondary
observations are reported.

## 2. Narrative references / 서술 레퍼런스

These sources influenced explanation order and terminology, not the run's score.
All run claims remain governed by the frozen local run spec and Harbor receipts.

| Source | Applied narrative pattern |
|---|---|
| [Seoul National University, staged design and validation study](https://s-space.snu.ac.kr/handle/10371/216109?mode=full) | State research questions first, then separate design, validation, field execution, and limitations. |
| [Anthropic, Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) | Define task, trial, grader, transcript/trajectory, outcome, evaluation harness, agent harness, and suite before presenting scores. |
| [OpenAI, GPT-4.5 System Card](https://cdn.openai.com/gpt-4-5-system-card.pdf) | Explain an agentic rollout as environment setup → agent action → task-specific test → success decision. |
| [Google DeepMind, Gemini technical report](https://deepmind.google/gemini/gemini_1_report.pdf) | Introduce the suite through capability/task families before dense benchmark tables. |
| [SpaceX, Starship User's Guide](https://www.spacex.com/media/starship_users_guide_v1.pdf) | Move from purpose to system composition, interfaces, operating environment, and constraints. Used only as a presentation-structure reference. |

## 3. Measurement units / 측정 단위

| Unit | Definition in this run |
|---|---|
| Suite | The frozen `Terminal-Bench 2.1 @6` catalog used by the run. |
| Task | One immutable task ID with its instruction, container image, resource/timeout rule, and canonical verifier. |
| Arm | One harness condition: GEODE or native Codex. Both arms use the same declared model route. |
| Repetition | One workload-aligned repeat of a task within an arm. Five repetitions were planned; the suite route provides no shared random-seed control. |
| Cell | The planned coordinate `(task, arm, repetition)`. `89 tasks × 2 arms × 5 repetitions = 890 cells`. A cell can be executed, infrastructure-invalid, or prospectively excluded. |
| Harbor job | An orchestration bundle containing one or more trials. It is not a score denominator. |
| Harbor trial | One task invocation with its own execution directory, result, agent outputs, verifier outputs, and logs. |
| Attempt | One append-only lineage row for an original execution, authorized supplement, or recorded batch/infrastructure incident. One cell may have multiple attempts, but only the frozen selection rule resolves it. |
| Valid selected cell | A cell resolved to a protocol-valid attempt. Verifier pass and verifier zero both remain valid observations. |
| Infrastructure-invalid | Execution evidence that cannot support a semantic pass/zero decision. It is never silently converted to zero. |
| Exact common cell | A task + repetition pair for which both arms have valid selected attempts. This run has 429 exact common pairs. |

The public numerator/denominator labels must always name the unit. `344/435`
means GEODE verifier passes over valid selected GEODE cells. `339/429 vs
331/429` means passes over the exact same common task+repetition pairs.

## 4. Evidence production workflow / 증거 생산 워크플로우

1. **Freeze** — record suite version, ordered tasks, model route, effort,
   time/resource limits, arm definitions, repetition count, concurrency,
   supplement rule, and privacy boundary before model calls.
2. **Preflight** — fail closed on authentication, task image, container,
   canonical verifier, disk, and resource availability.
3. **Execute in isolation** — Harbor creates fresh task trials. GEODE and native
   Codex run under the same task-side contract.
4. **Measure outcome** — Harbor result plus the canonical verifier receipt owns
   pass/zero/invalid classification.
5. **Capture behavior** — the agent emits ATIF when available. Raw terminal
   payloads and provider-private reasoning remain outside public derivatives.
6. **Preserve lineage** — append original attempts, invalid attempts, and any
   prospectively authorized supplements to `attempts.jsonl`; never rewrite raw
   evidence or create a second raw store.
7. **Refine** — normalize selected behavior into `geode.trajectory@1`, minimize
   payloads, bind every retained source by path and SHA-256, and derive replay
   views with `score_authority=false`.
8. **Analyze** — build verifier receipts, outcomes, native results, and analysis
   from the frozen selection rule. Recompute every numerator and denominator
   from the attempt-level ledger.
9. **Validate** — run schema validation, source-hash checks, full video decode,
   and secret, PII, identity, and host-local-path scans. Visually inspect both
   language variants at rendered pixels.
10. **Publish and read back** — copy only the publication allowlist to an
    append-only run-ID prefix, merge through review, then download the immutable
    commit bytes and verify SHA-256 and byte counts again.

## 5. Authority lanes / 권위 분리

| Lane | Flow | Claim ceiling |
|---|---|---|
| Score authority | isolated trial → Harbor result → canonical verifier → validity/outcome → analysis | Determines pass, zero, invalid, numerator, and denominator. |
| Behavior evidence | agent events → private ATIF → normalized trajectory → derived replay | Explains visible behavior and lineage; does not create reward. |
| Procedure evidence | observer-side PTY → sanitized transcript/video | Shows batch operation and monitoring; not one-to-one with cells and not score authority. |
| Publication proof | allowlist → schema/hash/privacy gates → immutable artifact commit → remote readback | Proves which reviewed bytes were published. |

## 6. Narrative spine and contents / 목차와 논리 전개

The contents slide is a claim map, not a page inventory. It exposes five core
messages first; the remaining scenes progressively disclose the mechanism,
evidence, operating condition, and limitation behind each message.

| Chapter | Core message shown up front | Evidence progressively disclosed later |
|---|---|---|
| 01. Why and what to measure | Pair two harnesses around the same model only after defining the unit and denominator. | research question → suite/task families → cell and exact-common definitions |
| 02. Where and how it runs | Execute one frozen contract inside one storage root and fresh-container boundaries. | storage ownership → host/Harbor/container isolation → preflight and run sequence |
| 03. What counts as evidence | Keep score authority separate from behavior evidence and join them by trial identity and digest. | raw result/verifier → attempt lineage → ATIF → normalized trajectory → derived replay |
| 04. Where it failed and what remains | Separate semantic zeroes, infrastructure invalids, and exclusions before comparing the same pairs. | failure schema → trace patterns → task ledger → exact-common result |
| 05. What can be published and claimed | Verify allowlisted bytes through immutable readback and publish the failed primary condition too. | privacy/hash gates → artifact commit → remote readback → supported/unsupported claims |

The researcher rail is `question → unit and control → denominator → limitation`.
The systems-engineer rail is `boundary → isolation → lineage → validation →
readback`. Together they enforce the same argument:
`constraint → boundary → mechanism → evidence → operating condition → decision`.

## 7. Video contract / 영상 계약

- One continuous upload: Korean first, then English.
- UTC is canonical in receipts; KST is the human-facing display time.
- Start with a contents scene whose five bullets are the video's core claims.
  Then progressively disclose motivation, data classes, Terminal-Bench task
  families, measurement units, storage root, isolation, Harbor capture
  semantics, run flow, attempt accumulation, trajectory refinement, failure
  patterns, exclusions, secondary results, publication, and claim boundaries.
- The eight pixel icons are an analyst grouping of the frozen 89 task IDs, not
  an official Terminal-Bench taxonomy.
- The 890-cell observation index consists of 870 executed cells and 20
  prospective exclusion cards. It must not imply 890 raw screen recordings.
- Derived casts reconstructed from ATIF are labelled derived replay. Observer
  PTY records are labelled procedure evidence. Neither is presented as a raw
  Harbor recording when no raw `recording.cast` exists.

## 8. Exclusions and result boundary / 제외와 결과 한계

- `terminal-bench/bn-fit-modify`: 5 repetitions × 2 arms. The unchanged
  official linux/amd64 verifier could not complete its SciPy import on the
  arm64 Rosetta host, including the prospectively preregistered thread-limit
  calibration.
- `terminal-bench/tune-mjcf`: 5 repetitions × 2 arms. The unchanged MuJoCo
  verifier dependency terminated with an illegal instruction before pytest
  collection on arm64 Docker Desktop.

These 20 cells are neither passes nor zeroes. A future x86_64 Linux study may
run them under the unchanged official images and verifiers, but its result must
remain a separately identified auxiliary study rather than a post-hoc patch to
this frozen run.
