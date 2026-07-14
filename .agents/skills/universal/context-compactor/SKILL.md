---
name: Context Compactor
description: Manages LLM context window size via boilerplate stripping and sliding windows.
---

# Router Alignment: Ephemeral Context Grounding

This rule permanently enforces inline payload mutation for all outbound text-model requests in the Agentic Application cascade.

## 1. Mandatory System Prompt Injection
- Every outbound `messages` payload sent to any cascade tier **must** include a `role: system` message at **index 0**.
- The canonical system message is defined in `src/capabilities/compaction.py` as the `SYSTEM_PROMPT` constant.
- No cascade tier is exempt. If a provider cannot accept `role: system`, the grounding text must be prepended as a prefix to the first `role: user` message instead.

## 2. Ephemeral Injection Only
- The system message is injected **at request time** inside the `ground_messages()` function. It is never persisted to disk, database, or session state.
- The original inbound `messages` array from the client must not be mutated. The router must operate on a **deep copy**.

## 3. Content Governance
- The `SYSTEM_GROUNDING_PROMPT` must identify the system as the "Agentic Application" and instruct the downstream model to respond helpfully and concisely.
- Any modification to the prompt content requires a corresponding entry in `retrospective.md` and a version bump.

## 4. Observability
- Every grounding injection must emit an `INFO`-level log line containing `[CONTEXT GROUNDING]` for SRE traceability.
- The log must include the number of messages in the grounded payload.

## 5. Relationship to Context Compaction
- After grounding is applied, the payload must pass through the **Context Compaction** layer defined in `40-phase-deploy.md`.
- Execution order: **Grounding (this rule)** → **Compaction** → **Admission Control** → **Cascade**.
- The system message injected by this rule is immune to compaction eviction (see `40-phase-deploy.md` §3).




# Context Compaction: v2.4.0 Specification

This rule enforces strict token conservation on all conversation payloads transiting the Agentic Application cascade. It eliminates wasteful verbosity, caps history depth, and mandates telemetry persistence.

## 1. Processing Pipeline (Mandatory Order)
All operations execute on a **deep copy** of the inbound messages array. The caller's data must never be mutated.

The 5-step sequence within `src/capabilities/compaction.py` is:
1. **Deep Copy** — `copy.deepcopy(messages)` at function entry.
2. **Grounding** — System prompt injected at index 0 (`ground_messages()`). See `20-00-phase-execute.md` §1.
3. **Prefix Stripping** — Verbose AI filler removed from `role: assistant` messages (`strip_boilerplate()`).
4. **Sliding Window** — Oldest messages beyond the cap are evicted (`apply_sliding_window()`).
5. **Cascade** — Compacted payload forwarded to `query_cloud()`. Admission Control (PRE-FLIGHT BYPASS) runs inside `llm_cloud.py`.

## 2. Prefix Stripping Rules
- Strip verbose AI conversational filler from `role: assistant` messages **only**.
- The following prefix patterns must be removed if they appear at the start of an assistant message:
  - `"Sure! "`, `"Sure, "`, `"Of course! "`, `"Of course, "`
  - `"Great question! "`, `"That's a great question! "`
  - `"Absolutely! "`, `"Certainly! "`
  - `"I'd be happy to help! "`, `"I'd be happy to help you with that! "`
  - `"Let me help you with that. "`
- Stripping is **prefix-only** and **case-sensitive**. The substantive content after the filler must be preserved verbatim.
- If stripping a prefix would result in an empty string, the original message must be kept intact.
- Multiple matching prefixes on the same message: strip only the **first** (longest) match.

## 3. Sliding Window Limit
- Hard cap: **10 messages** in any outbound payload (including the `role: system` message).
- The `role: system` message at index 0 is **pinned** and never evicted.
- When the payload exceeds 10 messages, retain only the system message + the **most recent 9** conversation messages. All older messages are dropped.

## 4. System Message Immunity
- The `role: system` message injected by `20-00-phase-execute.md` is **exempt** from both sliding window eviction and boilerplate stripping.
- It must always occupy index 0 of the outbound payload.

## 5. Observability
- Every compaction event must emit an `INFO`-level log line containing `[CONTEXT COMPACTION]`.
- The log must include:
  - The **before** and **after** message counts (e.g., `"Compacted 24 → 10 messages"`).
  - The number of boilerplate prefixes stripped (e.g., `"Stripped 3 filler prefixes"`).
- If no compaction was necessary (payload already within limits and no boilerplate found), no log line is emitted.

## 6. Telemetry Persistence
- Every request must record compaction metrics to `data/pipeline_metrics.db` (DuckDB).
- Required fields: `raw_tokens`, `compact_tokens`, `tokens_saved`, `savings_pct`, `messages_dropped`, `prefixes_stripped`, `latency_sec`, `tier`.
- The DuckDB connection must follow the DuckDB Optimizer skill directives: WAL mode enabled, memory capped at 256MB.
- Telemetry writes must be non-blocking to the request path — a failed write must not crash the cascade.
