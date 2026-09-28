# Phase 0 Research: Ticket Readiness Checker

The project constitution and this round's user input already fix the stack and several
implementation approaches (Python 3.12, Streamlit, Groq API returning JSON, rubric with
weights in `rubric.yaml`, pytest for the JSON parser and score calculation, no database,
no auth). No `NEEDS CLARIFICATION` markers remain in the Technical Context. The research
below resolves the remaining implementation-approach questions needed before design.

## 1. How to get structured (six-criteria) output from the Groq API

**Decision**: Send one Groq API call per evaluation, with the rubric (from
`rubric.yaml`, including weights) and the pasted ticket text in the prompt, and request a
JSON response (Groq's OpenAI-compatible `response_format={"type": "json_object"}` mode on
supported models) containing a score (0-100) and a missing-items list per criterion.

**Rationale**: A single call keeps latency low (supports SC-001's 15-second target) and
keeps `groq_client.py` a thin, single-purpose wrapper. JSON-mode output removes the need
for brittle free-text parsing and gives `parsing.py` a well-defined, testable input shape
— directly matching this round's explicit instruction ("Groq API for scoring, response as
JSON" / "pytest for the JSON parser").

**Alternatives considered**:
- *One API call per criterion (6 calls)*: More granular but 6x the latency and cost;
  risks blowing the 15-second target. Rejected.
- *Free-text response parsed with regex*: Fragile against minor wording changes in model
  output. Rejected in favor of JSON-mode.

## 2. Which Groq model to use

**Decision**: Default to a current general-purpose, instruction-following Groq-hosted
model, configurable via an environment variable (`GROQ_MODEL`) with that default — not
hardcoded as a single unconfigurable literal.

**Rationale**: Groq's available models change over time; hardcoding one model string
would require a code change every time Groq deprecates a model. An env-var-with-default
keeps the zero-configuration case working while leaving an escape hatch. This does not
conflict with Constitution Principle IV (which governs the *rubric*, not the model
identifier).

**Alternatives considered**:
- *Hardcode one specific model string*: Simplest, but brittle against upstream model
  deprecation. Rejected.
- *Let the user pick a model in the UI*: Adds UI surface not requested and out of scope
  for a single-page, minimal, no-auth tool. Rejected.

## 3. Rubric config file: format, location, and weights

**Decision**: YAML, at the repository root as `rubric.yaml` (not nested under a
`config/` directory), with an explicit per-criterion `weight` field. The overall score is
the weighted average of the six criterion scores, using these weights, rounded to the
nearest integer.

**Rationale**: YAML handles multi-line, human-readable criterion descriptions and
comments better than JSON/TOML for this shape of data. The file location and the
inclusion of weights follow this round's explicit instruction ("Rubric with weights in
rubric.yaml"). Weights let the tool reflect that, for delegating work to an AI coding
agent, some criteria (e.g., acceptance criteria, scope) may matter more than others to
overall readiness — without hardcoding that judgment into `scoring.py`.

This refines (not contradicts) the spec's Assumptions section, which states the overall
score is "the average of the six criterion scores *unless a more specific aggregation is
requested later*" — a weighted average using rubric-defined weights is exactly that more
specific aggregation, now requested.

**Weight normalization rule**: weights in `rubric.yaml` need not sum to 1 or 100;
`scoring.py` MUST normalize them (each weight ÷ sum of all weights) before computing the
weighted average, so any positive relative weighting scheme works without the rubric
author needing to hand-balance the numbers.

**Alternatives considered**:
- *Simple (unweighted) average*: Was the prior default before weights were requested;
  superseded by this round's explicit instruction. Rejected for this iteration.
- *JSON or TOML for the rubric*: Less readable for multi-line descriptions. Rejected.
- *`config/rubric.yaml`*: A nested config directory was the prior plan's location;
  superseded by this round's explicit `rubric.yaml` (repo root) instruction.

## 4. Response validation strategy

**Decision**: Validate the parsed JSON in `parsing.py` with plain Python (explicit key
checks, type checks, range checks for the 0-100 score) — no schema-validation library
(e.g., pydantic, jsonschema) added as a new dependency.

**Rationale**: The shape is small and fixed (six named criteria, each with a score and a
list of strings); hand-written validation keeps the dependency list minimal, and is
exactly what the required pytest unit tests need to cover — malformed input, out-of-range
scores, missing criteria.

**Alternatives considered**:
- *pydantic model*: Nice ergonomics but an added dependency for a validation surface this
  small. Rejected.

## 5. Short-input and long-input handling (FR-013, FR-014)

**Decision**: Before calling the Groq scoring prompt, a lightweight pre-check step
(itself using the same Groq call, via a distinct response field/flag, rather than a
separate heuristic like word count) classifies the pasted text as: (a) too short to
identify any criteria, (b) plausibly containing multiple distinct tickets, or (c) a
single scoreable ticket. Case (a) short-circuits to a format-guidance message (FR-013,
no criterion scores). Case (b) short-circuits to a proposed split (FR-014, no criterion
scores for the combined text). Case (c) proceeds to normal scoring.

**Rationale**: The spec's Assumptions section explicitly says this boundary is
"judged on content, not a fixed word/character count" and "expected to rely on the same
evaluation step used for scoring" — a fixed word-count threshold would be a hardcoded
heuristic that misclassifies (e.g., a terse-but-complete one-line ticket vs. a rambling
100-word ticket with no goal). Folding the classification into the same LLM call/response
schema keeps this a single round-trip, preserving the SC-001 latency target, and avoids
a second hardcoded ruleset in `scoring.py`.

**Alternatives considered**:
- *Fixed word/character count thresholds*: Simple and fully deterministic (easy to unit
  test), but the spec explicitly rejects a fixed-count boundary in favor of a
  content-based judgment. Rejected.
- *Separate API call just for classification*: Doubles latency for every check. Rejected
  in favor of a single call whose JSON response includes a status field
  (`ok` / `too_short` / `too_long`) alongside scores when `status == "ok"`.

## 6. Session / re-check behavior (User Story 3)

**Decision**: Use Streamlit's default `st.session_state` scoped to the browser session to
hold the last evaluation result (or guidance message), cleared automatically when the
session ends. Re-running the check overwrites the stored result. No database.

**Rationale**: Satisfies FR-007 (re-run replaces previous results) and FR-011 / the "no
database" instruction with no additional storage layer.

**Alternatives considered**: Any file/database-backed persistence — explicitly out of
scope. Rejected.

## 7. Error handling for API failures

**Decision**: `groq_client.py` raises a small, specific exception on failure (timeout,
auth error, rate limit, malformed response); `app.py` catches it at the call site and
renders `st.error(...)` with an actionable message, never a partial/fabricated score.

**Rationale**: Directly satisfies FR-009 and the "scoring service unavailable" edge case.

**Alternatives considered**: Swallow errors and show a default/zero score — would violate
FR-009. Rejected.

## Output

All Technical Context items are resolved; no `NEEDS CLARIFICATION` markers remain.
Proceeding to Phase 1 design.
