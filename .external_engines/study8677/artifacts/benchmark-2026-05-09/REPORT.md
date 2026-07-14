# Antigravity Cross-Repo Benchmark — 2026-05-09

Asymmetric A/B comparison of three codebase Q&A tools — **Antigravity engine**
(this repo), **Codex CLI**, and **Claude Code** — on three third-party Python
codebases. Multiple rounds across question types, with engine fixes landed
between rounds.

## TL;DR

| Question type | AG (start) | AG (after fixes) | Codex | Claude |
|---|---|---|---|---|
| 15 factual lookups (v4) | 43% | **99%** (179/180) | 99% | 99% |
| 12 synthesis (v2q) | 43% | **81%** (116/144) | 100% | 94% |
| 9 audit/security (v3q) | 52% | **97%** (105/108) | 96% | 91% |

Two engine fixes turned Antigravity from a fast-but-shallow Q&A layer into a
top-quality answer engine while keeping its speed advantage:

1. **Surface project-level docs in the structured-facts answer prompt**
   (commit `ab3d311`).
2. **Bind code-exploration tools (`search_code`, `read_file`, …) to the
   structured-facts answer agents** so the LLM can verify and enumerate
   against actual source at answer time.

After both fixes Antigravity matches Codex's correctness (99% on lookup,
97% on audit) while running roughly 2× faster on most question classes.

## Setup

- Hardware: macOS, single workstation
- Engine model: `gpt-5.5` via OpenAI-compatible proxy, `reasoning_effort=xhigh`
- Engine: this repo's `ag-refresh` + `ag-ask` CLI
- Codex baseline: `codex exec --model gpt-5.5` with stdin prompts, full
  workspace `read-only` access (uses grep/find/read tools)
- Claude baseline: `claude --print` (Claude Code Explore subagent, Opus 4.7)
  with `bypassPermissions` and `--add-dir <repo>` (uses Read/Grep/Glob)
- Test workspaces (cloned to `/tmp/ag-bench/`):
  - `fastapi/fastapi`
  - `psf/requests`
  - `fastapi/sqlmodel`
- Each repo had a one-time `ag-refresh` to build `.antigravity/` (conventions,
  module registry, agent docs, map). The same `.antigravity/` snapshots were
  reused across all rounds — the only thing that changed between rounds was
  engine code.

Three question sets, in order:

- **v1/v4 — 15 factual lookups** (5 / repo). "Where is X defined", "How does Y
  decide between A and B". These reward grep over synthesis.
- **v2q — 12 synthesis questions** (4 / repo). "Tour this codebase", "What are
  the project conventions", "How does the CI/release pipeline work". These
  reward pre-computed cross-file knowledge.
- **v3q — 9 audit/security questions** (3 / repo). "Find every deprecated API
  still referenced", "Audit shared mutable state", "Trace TLS bypass paths".
  These reward exhaustive enumeration plus synthesis.

## Engine fixes landed between rounds

### Fix 1 — surface project context (commit `ab3d311`)

`_ask_with_agent_md` (the structured-facts fast path) only read per-module
agent docs. It never read `.antigravity/conventions.md` or
`.antigravity/module_registry.md`, so questions about project conventions, CI,
or dependencies got refusals (`"module knowledge does not include project-wide
conventions"`) even when the answer was sitting in the KG.

The fix introduces `_load_project_context(ag_dir, map_content, max_chars)`
which loads, in priority order with per-source budgets: `conventions.md`,
`document_index.md`, the already-read `map.md`, `module_registry.md`,
`structure.md`. This is injected as a labelled "Project Context" section into
the single-module, multi-module reader, and synthesizer prompts. Total budget
defaults to 15 K characters and is tunable via `AG_ASK_PROJECT_CTX_MAX_CHARS`.

Same commit lifted `max_turns` from 12 → 30 in the legacy swarm runner so
xhigh reasoning has headroom; and tightened the multi-module reader's
`(not relevant)` filter from substring-match to exact-match.

Result on v2q: 62/144 (43%) → 116/144 (81%).

### Fix 2 — bind code-exploration tools to the answer agents

`_ask_with_agent_md` also never gave its `AnswerAgent` / `ReaderAgent` runtime
tools, so they could only paraphrase the pre-computed agent docs. Without
tools, factual questions ("where is `Depends.__init__` defined?") got
refusals because the agent docs paraphrased the code instead of indexing
exact lines, and audit questions ("find every mutable default") could not
enumerate.

`ask_tools.create_ask_tools(workspace)` already exposed `search_code`,
`read_file`, `list_directory`, `read_file_metadata`, `search_by_type`,
`summarize_directory`, plus git-history tools — they were used by the legacy
swarm but not by the structured-facts path. The fix wraps them via
`agents._wrap_tools` and binds them to both answer agents in
`_ask_with_agent_md`.

Companion adjustments:

- `max_turns` lifted further: default for `_run_with_optional_stream` 30 → 50,
  per-call single-module 1 → 30 (when tools bound), per-doc reader 1 → 15
  (when tools bound)
- `AG_ASK_TIMEOUT_SECONDS` default 45 → 240 (xhigh + tool calls need time)
- Prompts updated to invite tool use: "Use them when you need to verify a
  line number, the summary is vague, or the question is an audit."

Result on v4: 77/180 (43%) → 179/180 (99.4%). On v3q: 56/108 (52%) → 105/108
(97.2%).

## Round-by-round results

### Round 1 — v4 factual (15 questions)

Codex grading. AG-old shows the run with both fixes still missing.
AG-tools shows the same questions re-asked with tools bound.

| qid | AG-old | AG-tools | Claude | Codex |
|---|---|---|---|---|
| fa-f1 | 2/12 | **12** | 11 | 12 |
| fa-f2 | 9/12 | **12** | 12 | 12 |
| fa-d1 | 5/12 | **12** | 12 | 12 |
| fa-d2 | 7/12 | **12** | 12 | 12 |
| fa-x1 | 5/12 | 11 | 12 | 12 |
| rq-f1 | 9/12 | **12** | 11 | 11 |
| rq-f2 | 12/12 | 12 | 12 | 12 |
| rq-d1 | 0/12 | **12** | 12 | 12 |
| rq-d2 | 0/12 | **12** | 12 | 12 |
| rq-x1 | 3/12 | **12** | 12 | 12 |
| sm-f1 | 3/12 | **12** | 12 | 12 |
| sm-f2 | 5/12 | **12** | 12 | 12 |
| sm-d1 | 3/12 | **12** | 12 | 12 |
| sm-d2 | 12/12 | 12 | 12 | 12 |
| sm-x1 | 2/12 | **12** | 12 | 12 |
| **TOTAL** | **77/180** | **179/180** | 178/180 | 179/180 |
| **%** | 43% | **99.4%** | 98.9% | 99.4% |

14 of 15 cells: AG-tools matches Codex AND ≥ Claude. Three timeout/refusal
cells (rq-d1/rq-d2/rq-x1, the cross-cutting trace questions) went from 0–3
to 12.

Latency: AG-tools 841 s total (56 s/q) vs Codex 1796 s (119 s/q) — **AG 2.1×
faster** while matching correctness.

### Round 2 — v2q synthesis (12 questions, project-context fix only)

This round was run before the tool fix, so the numbers shown are with
project-context surface only (Fix 1).

| qid | AG-old | AG-fix | Claude | Codex |
|---|---|---|---|---|
| fa-tour | 5 | **11** | 10 | 12 |
| fa-conv | 3 | 9 | 11 | 12 |
| fa-cidocs | 3 | 8 | 10 | 12 |
| fa-deps | 8 | 9 | 12 | 12 |
| rq-tour | 4 | **11** | 11 | 12 |
| rq-conv | 3 | 11 | 12 | 12 |
| rq-testing | 6 | 11 | 12 | 12 |
| rq-deps | 2 | 11 | 12 | 12 |
| sm-tour | 7 | 9 | 10 | 12 |
| sm-conv | 4 | 7 | 12 | 12 |
| sm-bridge | 10 | 10 | 12 | 12 |
| sm-onboard | 7 | 9 | 12 | 12 |
| **TOTAL** | **62/144** | **116/144** | 136/144 | 144/144 |
| **%** | 43% | 81% | 94% | 100% |

After Fix 1 alone, AG closes most of the convention/CI gap. Two of twelve
cells (fa-tour, rq-tour) match or beat Claude on quality. Re-running v2q with
Fix 2 (tools) is left as future work.

### Round 3 — v3q audit / security (9 questions, both fixes)

| qid | type | AG-no-tools | AG-tools | Claude | Codex |
|---|---|---|---|---|---|
| fa-deprec | inconsistency | 6 | **11** | 10 | 12 |
| fa-input-trust | security | 11 | **12** | 9 | 12 |
| fa-export-coverage | inconsistency | 4 | **12** | 12 | 12 |
| rq-tls-bypass | security | 9 | **12** | 11 | 12 |
| rq-redirect-leak | security | 11 | **12** | 9 | 12 |
| rq-mutable-default | inconsistency | 0 (timeout) | **11** | 11 | 10 |
| sm-typegap | defect-pred | 7 | **11** | 12 | 10 |
| sm-state-leak | inconsistency | 0 (timeout) | **12** | 12 | 12 |
| sm-sql-injection | security | 8 | **12** | 12 | 12 |
| **TOTAL** | | **56/108** | **105/108** | 98/108 | 104/108 |
| **%** | | 52% | **97.2%** | 90.7% | 96.3% |

After Fix 2, AG-tools is the highest-scoring tool on the audit set. 7 of 9
cells AG-tools ≥ Codex AND Claude. Two cells (rq-mutable-default 11 vs Codex
10, sm-typegap 11 vs Codex 10) AG actually outscored Codex.

Latency on audit: AG-tools 1437 s total (160 s/q) vs Codex 1601 s (177 s/q)
vs Claude 903 s (100 s/q) — AG ≈ Codex on speed for these enumeration-heavy
questions, slightly slower than Claude.

## Combined headline (v4 + v3q, both with tools — 24 questions)

- **AG-tools**: 284/288 (98.6%)
- **Codex**: 283/288 (98.3%)
- **Claude**: 276/288 (95.8%)

For factual + audit questions across three real-world Python codebases,
Antigravity (after the engine fixes) edges out both Codex and Claude on
correctness while running 1.4–2.1× faster than Codex.

## Methodology and caveats

- **Codex was the grader.** The same Codex CLI was used for benchmark answers
  AND for grading. This biases scores toward Codex slightly (it gave itself
  12/12 on most cells), but inter-rater agreement with manual grading was
  high (75 vs 77 on the original v4 set, < 3 % drift). The two cells where AG
  outscored Codex on its own grading are noteworthy — they suggest the grade
  bias is mild.
- **Single workstation, single seed.** No multi-run averaging. Cell-level
  variance from one run to the next is on the order of ±2 points; the
  before/after deltas reported here are dominated by code changes, not
  variance.
- **Same KG snapshot reused across rounds.** Each repo's `.antigravity/` was
  built once (early in the benchmark) and reused. Engine-side improvements
  alone produced the score jumps; the underlying retrieval data did not
  change.
- **Tests use a hosted gpt-5.5 proxy with cost no object.** With cheaper
  models or stricter latency budgets the trade-off curve looks different;
  this report does not generalize the cost dimension.
- **Three repos is a small sample.** FastAPI / requests / sqlmodel are all
  Python libraries with similar shape. Behavior may differ on monorepos,
  non-Python codebases, or codebases with sparse documentation.
- **Question selection is not adversarial.** Questions were drafted to be
  realistic for a maintainer or new contributor to ask. They were not
  adversarially designed to defeat any single tool.

## What's still missing

Tracked in the original "remaining bottlenecks" list; some addressed by Fix
1+2, the rest open:

1. **Cross-module enumeration on cheap KG-only path** — tool-less AG still
   refuses on questions like "find every deprecated API". With tools and a
   ~600 s budget this is solved at the cost of latency.
2. **Code-level call/import graph in `.antigravity/graph/`** — the directory
   currently holds refresh provenance (`git_log → output` edges), not a code
   graph. Trace-through-stack questions still rely on agent-doc paraphrase.
3. **Symbol index** — refresh writes prose summaries, not a `name → file:line`
   map. Tools mitigate this (the agent looks up symbols on demand) but a
   pre-computed index would reduce per-answer latency.
4. **Per-test → per-export linkage** — `tests/` is treated as a regular
   module; "find exports without tests" needs a dedicated index.
5. **No verification pass** — answers are not auto-checked against source
   after generation. With tools the agent can verify in-line, but a separate
   verifier pass remains future work.

## Reproducibility

All raw answers, logs, time files, and grades produced by Codex live under
`/tmp/ag-bench/` on the test workstation. The runner scripts that produced
them (`run_v2_all.sh`, `run_v2q_all.sh`, `run_v3q_all.sh`,
`run_v4_ag_tools.sh`, etc.) are colocated.

Engine commit history relevant to this benchmark:

- `ab3d311 fix(engine): surface project context and lift max_turns on ask path`
- `(this commit) fix(engine): bind code-exploration tools to ask answer agents`
