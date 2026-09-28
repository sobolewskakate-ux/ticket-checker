# Phase 1 Data Model: Ticket Readiness Checker

These are in-memory structures for a single evaluation; nothing here is persisted (no
database — Constitution + spec FR-011 + this round's explicit "no database" instruction).
They exist for the lifetime of one `st.session_state` entry.

## TicketSubmission

The raw text pasted by the user for one evaluation.

| Field | Type | Notes |
|---|---|---|
| `text` | `str` | Full pasted ticket text. Required, non-empty (empty input is rejected before scoring — see Edge Cases in spec.md). |

## RubricCriterion (config-defined, not runtime data)

One entry in `rubric.yaml`, describing one of the six fixed criteria.

| Field | Type | Notes |
|---|---|---|
| `key` | `str` | Stable identifier, one of: `goal`, `acceptance_criteria`, `scope`, `dependencies`, `test_plan`, `constraints`. |
| `label` | `str` | Human-readable name shown in the UI (e.g., "Acceptance Criteria"). |
| `description` | `str` | What this criterion evaluates — sent to the LLM as scoring guidance. |
| `weight` | `number` | Relative weight used to compute the overall score. Need not sum to 1 or 100 across criteria — `scoring.py` normalizes (see contracts/scoring-interface.md). Must be > 0. |
| `missing_item_examples` | `list[str]` | Optional example phrasing to guide what a "missing item" looks like for this criterion. |

**Validation rule**: `rubric.yaml` MUST define exactly six criteria with the six `key`
values above, each with a positive `weight` (Constitution Principle IV — rubric and its
weights live in config; the app must fail fast with a clear error if the config is
malformed or incomplete, rather than guessing).

## CriterionScore

The result for one criterion, for one `TicketSubmission` that was scoreable (see
`EvaluationOutcome` below).

| Field | Type | Notes |
|---|---|---|
| `key` | `str` | Matches a `RubricCriterion.key`. |
| `score` | `int` | 0-100 inclusive. |
| `missing_items` | `list[str]` | Non-empty only when `score < 50` (FR-005, FR-006); empty list when `score >= 50`. |

**Validation rules** (enforced in `parsing.py`, covered by unit tests per Constitution
Principle III):
- `score` MUST be an integer in `[0, 100]`; out-of-range or non-numeric values from the
  LLM response are a parsing error, not silently clamped.
- `missing_items` MUST be empty when `score >= 50` (FR-006) — if the LLM returns items
  anyway, `parsing.py` drops them; the FR-006 contract is authoritative over the raw
  response.
- All six expected `key` values MUST be present; a missing criterion in the response is a
  parsing error surfaced via FR-009, not a silently-skipped criterion.

## ReadinessAssessment

The full result of one *scoreable* evaluation, built from six `CriterionScore` entries
and the rubric's weights.

| Field | Type | Notes |
|---|---|---|
| `criterion_scores` | `list[CriterionScore]` | Exactly six entries, one per rubric criterion. |
| `overall_score` | `int` | 0-100; weighted average of the six `CriterionScore.score` values using each `RubricCriterion.weight` (normalized), rounded to the nearest integer. |

## EvaluationOutcome

The top-level result `scoring.py` returns to `app.py` for any check — covers the normal
scoring path and the two guidance paths (FR-013, FR-014).

| Field | Type | Notes |
|---|---|---|
| `status` | `str` | One of `ok`, `too_short`, `too_long`. |
| `assessment` | `ReadinessAssessment \| None` | Present only when `status == "ok"`. |
| `guidance_message` | `str \| None` | Present only when `status == "too_short"` (explains expected format, names the six criteria) or `status == "too_long"` (proposes a split). |
| `proposed_split` | `list[str] \| None` | Present only when `status == "too_long"` — the proposed individual ticket texts, in order, for the user to copy and re-run one at a time. |

This is what `app.py` renders; it is held in `st.session_state` only for the current
session (no database) and is fully replaced on each re-check (User Story 3 / FR-007).

## Relationships

```text
TicketSubmission (1) ──evaluated against──> RubricCriterion (6, from rubric.yaml)
                                                   │
                              ┌────────────────────┼────────────────────┐
                              ▼                    ▼                    ▼
                       status = ok         status = too_short    status = too_long
                              │                    │                    │
                              ▼                    ▼                    ▼
                    CriterionScore (6)      guidance_message     guidance_message +
                              │                                    proposed_split
                              ▼
                    ReadinessAssessment (1)
                    (weighted overall_score)
```
