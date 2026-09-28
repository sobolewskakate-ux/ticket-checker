---

description: "Task list template for feature implementation"
---

# Tasks: Ticket Readiness Checker

**Input**: Design documents from `/specs/001-ticket-readiness-checker/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md (all present)

**Tests**: Included and REQUIRED — the project constitution (Principle III) and this
feature's plan explicitly require pytest unit tests for the JSON response parser
(`parsing.py`) and the score calculation (`scoring.py`). Streamlit UI code in `app.py` is
exempt from unit-test coverage per the constitution and is instead verified via
`quickstart.md`.

**Organization**: Tasks are grouped by user story (from spec.md: US1 and US2 are both
P1, US3 is P2) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths are included in every description

## Path Conventions

Single flat Python project at the repository root (per plan.md's Structure Decision — no
`src/` nesting, no frontend/backend split, no auth, no database):
`app.py`, `scoring.py`, `parsing.py`, `groq_client.py`, `rubric.yaml`, `tests/unit/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create the project skeleton at the repository root per plan.md's Project
      Structure: empty `app.py`, `scoring.py`, `parsing.py`, `groq_client.py`,
      `rubric.yaml`, and a `tests/unit/` directory
- [ ] T002 Create `requirements.txt` at the repository root listing `streamlit`, `groq`,
      `pyyaml`, and `pytest`
- [ ] T003 [P] Create `.env.example` at the repository root with a single line
      `GROQ_API_KEY=your-key-here` (placeholder only) and a `.gitignore` at the
      repository root excluding `.env`, `.venv/`, and `__pycache__/`

**Checkpoint**: Repo skeleton exists; no code logic yet.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared config, data structures, and the Groq wrapper that every user story
depends on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Populate `rubric.yaml` at the repository root with exactly six criteria —
      `key` values `goal`, `acceptance_criteria`, `scope`, `dependencies`, `test_plan`,
      `constraints` — each with a `label` (str), `description` (str), and `weight`
      (number, MUST be > 0), per contracts/rubric-config.md
- [ ] T005 [P] In `scoring.py`, implement the `RubricCriterion` and `CriterionScore`
      dataclasses per data-model.md (`CriterionScore.score`: int in `[0, 100]`;
      `CriterionScore.missing_items`: list[str], non-empty only when `score < 50`) and a
      `RubricConfigError` exception class
- [ ] T006 [P] In `parsing.py`, implement the `ReadinessAssessment` and
      `EvaluationOutcome` dataclasses per data-model.md (`EvaluationOutcome.status`: one
      of `"ok"`, `"too_short"`, `"too_long"`; `assessment` present only when
      `status == "ok"`; `guidance_message` present when `status` is `"too_short"` or
      `"too_long"`; `proposed_split` present only when `status == "too_long"`) and a
      `ParsingError` exception class
- [ ] T007 [P] In `groq_client.py`, implement `get_completion(prompt: str) -> str`: read
      `GROQ_API_KEY` (required) and `GROQ_MODEL` (optional, with a default) from
      `os.environ` — never as a parameter default — call the Groq API with
      `response_format={"type": "json_object"}`, and raise a `ScoringServiceError` on a
      missing/invalid API key, timeout, rate limit, or non-2xx response
- [ ] T008 In `scoring.py`, implement `load_rubric(path: str = "rubric.yaml") ->
      list[RubricCriterion]`: parse the YAML, validate it defines exactly the six
      required `key` values each with a non-empty `label`, `description`, and a
      `weight > 0`, and raise `RubricConfigError` with a clear message when the file is
      missing, malformed, or incomplete, per contracts/rubric-config.md (depends on T005
      for `RubricCriterion`/`RubricConfigError`)

**Checkpoint**: Config, shared data types, and the Groq wrapper exist — user story
implementation can now begin.

---

## Phase 3: User Story 1 - Score a pasted ticket (Priority: P1) 🎯 MVP

**Goal**: A user pastes a ticket and receives a 0-100 score for each of the six criteria
plus a weighted overall score — or, when the input is too short or too long to score
directly, actionable guidance instead (FR-013, FR-014).

**Independent Test**: Paste a well-specified ticket and confirm all six scores plus an
overall score appear within ~15 seconds; paste a single word and confirm format guidance
appears instead of scores; paste text bundling multiple tickets and confirm a proposed
split appears instead of a single score.

### Tests for User Story 1 ⚠️

> Write these tests FIRST; they MUST fail before the corresponding implementation task.

- [ ] T009 [US1] Unit test in `tests/unit/test_parsing.py`: `parse_response()` given a
      valid `status: "ok"` JSON response with all six criteria returns an
      `EvaluationOutcome` with `status == "ok"` and six `CriterionScore` entries with the
      expected `key`/`score`/`missing_items` values
- [ ] T010 [US1] Unit test in `tests/unit/test_parsing.py`: `parse_response()` raises
      `ParsingError` when `raw_text` is not valid JSON
- [ ] T011 [US1] Unit test in `tests/unit/test_parsing.py`: `parse_response()` raises
      `ParsingError` when `status == "ok"` and a required criterion `key` is missing from
      the response
- [ ] T012 [US1] Unit test in `tests/unit/test_parsing.py`: `parse_response()` raises
      `ParsingError` when a criterion's `score` is non-numeric or outside `[0, 100]`
- [ ] T013 [US1] Unit test in `tests/unit/test_parsing.py`: `parse_response()` given a
      `status: "too_short"` JSON response returns an `EvaluationOutcome` with
      `status == "too_short"`, `assessment is None`, and a non-empty `guidance_message`
- [ ] T014 [US1] Unit test in `tests/unit/test_parsing.py`: `parse_response()` given a
      `status: "too_long"` JSON response returns an `EvaluationOutcome` with
      `status == "too_long"`, `assessment is None`, a non-empty `guidance_message`, and a
      non-empty `proposed_split` list
- [ ] T015 [P] [US1] Unit test in `tests/unit/test_scoring.py`:
      `compute_overall_score()` given six `CriterionScore` values and a rubric with
      distinct weights returns the normalized-weight average rounded to the nearest
      integer, verified against a hand-calculated example

### Implementation for User Story 1

- [ ] T016 [P] [US1] In `parsing.py`, implement `parse_response(raw_text: str,
      expected_keys: list[str]) -> EvaluationOutcome` per contracts/scoring-interface.md,
      satisfying T009-T014: parse and validate the `status` field, validate all six
      criteria and score ranges for `status == "ok"`, validate `guidance_message` /
      `proposed_split` for the other two statuses, and raise `ParsingError` on any
      violation
- [ ] T017 [P] [US1] In `scoring.py`, implement `compute_overall_score(criterion_scores:
      list[CriterionScore], rubric: list[RubricCriterion]) -> int` per
      contracts/scoring-interface.md, satisfying T015: normalize weights
      (`weight_i / sum(all weights)`) and return
      `round(sum(score_i * normalized_weight_i))`
- [ ] T018 [US1] In `scoring.py`, implement `score_ticket(ticket_text: str, rubric:
      list[RubricCriterion]) -> EvaluationOutcome`: build a prompt embedding each
      criterion's `label`/`description`/`weight` and `ticket_text`, call
      `groq_client.get_completion()`, call `parsing.parse_response()`, and attach
      `overall_score` via `compute_overall_score()` when `status == "ok"`; propagate
      `ScoringServiceError`/`ParsingError` (depends on T007, T016, T017)
- [ ] T019 [US1] In `app.py`, render a `st.text_area` for pasting ticket text (FR-001)
      and a "Check ticket" button that, on click, calls `scoring.score_ticket()` while
      showing a loading indicator (e.g., `st.spinner`) for the duration of the call
      (FR-002, FR-008)
- [ ] T020 [US1] In `app.py`, guard the button handler: when the pasted text is empty or
      whitespace-only, show a prompt to enter ticket text and skip calling
      `scoring.score_ticket()` entirely (Edge Case in spec.md)
- [ ] T021 [US1] In `app.py`, when the result's `status == "ok"`, render all six
      `CriterionScore` entries (label + score) and the `overall_score` (FR-003, FR-004)
- [ ] T022 [US1] In `app.py`, when the result's `status == "too_short"`, render
      `guidance_message` (explaining the expected format and naming all six criteria)
      instead of any scores (FR-013)
- [ ] T023 [US1] In `app.py`, when the result's `status == "too_long"`, render
      `guidance_message` and the `proposed_split` list, and suggest the user copy each
      proposed ticket and re-run the check individually (FR-014)
- [ ] T024 [US1] In `app.py`, wrap the `scoring.score_ticket()` call in a
      try/except for `RubricConfigError`, `ScoringServiceError`, and `ParsingError`, and
      render `st.error(str(exc))` instead of any partial or fabricated result (FR-009)

**Checkpoint**: User Story 1 is fully functional and independently testable (MVP).

---

## Phase 4: User Story 2 - See what's missing for weak criteria (Priority: P1)

**Goal**: For every criterion scoring below 50, the user sees the specific items missing
for that criterion; no missing-items list is ever shown for a criterion scoring 50 or
above.

**Independent Test**: Check a ticket with at least one criterion below 50 and confirm a
missing-items list appears only under that criterion; check a ticket where all six
criteria score 50+ and confirm no missing-items lists appear anywhere.

### Tests for User Story 2 ⚠️

- [ ] T025 [US2] Unit test in `tests/unit/test_parsing.py`: `parse_response()` forces a
      criterion's `missing_items` to `[]` when its `score >= 50`, even if the raw
      response included items for it (FR-006)
- [ ] T026 [US2] Unit test in `tests/unit/test_parsing.py`: `parse_response()` preserves
      the raw `missing_items` list unchanged for a criterion when its `score < 50`
      (FR-005)

### Implementation for User Story 2

- [ ] T027 [US2] In `app.py`, under each rendered `CriterionScore` (from T021) with
      `score < 50`, render its `missing_items` as a bulleted list; render no
      missing-items block at all for any criterion with `score >= 50` (FR-005, FR-006)

**Checkpoint**: User Stories 1 and 2 both work independently.

---

## Phase 5: User Story 3 - Revise and re-check a ticket (Priority: P2)

**Goal**: After editing the pasted ticket text, re-running the check fully replaces the
previous results with results for the new text.

**Independent Test**: Run a check, edit the pasted text, run the check again, and confirm
the displayed scores/missing-items/guidance are fully replaced with no leftover state
from the previous check.

### Implementation for User Story 3

- [ ] T028 [US3] In `app.py`, store the current `EvaluationOutcome` in
      `st.session_state` and overwrite it in place on each "Check ticket" click, so that
      re-running the check with edited text fully replaces the previously rendered
      scores, missing-items, and guidance with no leftover state (FR-007)

**Checkpoint**: All user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T029 [P] Run `pytest tests/unit -v` and confirm every test in
      `tests/unit/test_parsing.py` and `tests/unit/test_scoring.py` passes
- [ ] T030 Execute the `quickstart.md` validation scenarios (User Stories 1-3, FR-013,
      FR-014, and error handling) end-to-end against the running app, per
      `specs/001-ticket-readiness-checker/quickstart.md`
- [ ] T031 [P] Verify `.env` is excluded via `.gitignore` and that no real
      `GROQ_API_KEY` value appears in any tracked file (Constitution Principle V)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational completion
  - US1 and US2 are both P1 and should ship together; US3 (P2) can follow
  - US2 depends on US1's `app.py` score rendering (T021) existing to attach missing-items
    display to; US3 depends on US1's button/results flow (T019, T021-T024) existing to
    wrap with session-state overwrite behavior
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### Within Each User Story

- Tests MUST be written first and MUST fail before their implementation task
- Shared data structures/config (Phase 2) before any story-specific logic
- `parsing.py`/`scoring.py` logic before `app.py` UI wiring
- Story complete and checkpointed before moving to the next priority

### Parallel Opportunities

- T003 can run in parallel with T002 (different files)
- T004, T005, T006, T007 can all run in parallel (four different files)
- T016 and T017 can run in parallel (different files: `parsing.py` vs. `scoring.py`)
- T015 can run in parallel with T009-T014 (different file: `test_scoring.py` vs.
  `test_parsing.py`)
- T029 and T031 can run in parallel (independent checks)

---

## Parallel Example: Foundational Phase

```bash
# After T001-T003 (Setup) complete, launch these four together:
Task: "Populate rubric.yaml with six criteria (key/label/description/weight)"
Task: "Implement RubricCriterion + CriterionScore dataclasses in scoring.py"
Task: "Implement ReadinessAssessment + EvaluationOutcome dataclasses in parsing.py"
Task: "Implement groq_client.get_completion() in groq_client.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 (T009-T024)
4. **STOP and VALIDATE**: run `pytest tests/unit -v`, then manually validate User Story 1
   in `quickstart.md`
5. Demo if ready — this alone delivers the core "paste a ticket, get scores" value

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. Add User Story 1 → validate independently → MVP
3. Add User Story 2 → validate independently (missing-items visibility)
4. Add User Story 3 → validate independently (edit-and-recheck loop)
5. Polish (Phase 6) → full `pytest` + `quickstart.md` pass

---

## Notes

- [P] tasks touch different files and have no unmet dependencies on each other
- [Story] label maps every user-story-phase task back to spec.md for traceability
- Tests are required for this feature (parsing + scoring logic) per the constitution —
  write them first and confirm they fail before implementing
- No task touches a database or an auth layer — this feature has neither
- Commit after each task or logical group; stop at any checkpoint to validate a story
  independently
