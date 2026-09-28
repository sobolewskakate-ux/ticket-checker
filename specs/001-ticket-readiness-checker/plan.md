# Implementation Plan: Ticket Readiness Checker

**Branch**: `001-ticket-readiness-checker` | **Date**: 2026-09-28 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-ticket-readiness-checker/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

A single-page Streamlit app where a user pastes a software ticket and receives a 0-100
score for each of six readiness criteria (goal, acceptance criteria, scope, dependencies,
test plan, constraints) plus a weighted overall score, with a list of missing items for
any criterion scoring below 50. Scoring is delegated to the Groq API, which is asked to
return a JSON response evaluated against a rubric — including per-criterion weights —
defined in `rubric.yaml` (never hardcoded). Text that is too short or that plausibly
contains multiple tickets is redirected to guidance instead of being scored (FR-013,
FR-014). No login, no persistence beyond the browser session, and no ticket-tracker
integration.

## Technical Context

**Language/Version**: Python 3.12 (fixed by project constitution)

**Primary Dependencies**: Streamlit (UI), `groq` Python SDK (LLM scoring calls, JSON
response), PyYAML (rubric config loading), pytest (tests)

**Storage**: N/A — no database, no persistence of ticket text, scores, or results beyond
the current browser session (per constitution, user input, and spec FR-011)

**Testing**: pytest, covering the JSON response parser and the score calculation (per
user input and constitution Principle III); Streamlit UI code in `app.py` is exempt from
unit-test coverage but is manually verified via the quickstart guide

**Target Platform**: Web browser, via a locally run (or self-hosted) Streamlit server

**Project Type**: Single-page web app (Streamlit) — single project, no frontend/backend
split, no auth

**Performance Goals**: End-to-end evaluation (paste → six scores + overall score
displayed) completes in under 15 seconds (SC-001), dominated by Groq API latency

**Constraints**: No user accounts/login, no database; no data persisted after the session
ends; no Jira/Linear/issue-tracker integration; `GROQ_API_KEY` MUST be read from an
environment variable and never hardcoded or committed; scoring rubric and its per-criterion
weights MUST live in `rubric.yaml`, not in code

**Scale/Scope**: Single ticket evaluated at a time, single user per session, six fixed
weighted criteria — small app, no concurrency or multi-tenancy concerns

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Status |
|---|---|---|
| I. Single-Page Simplicity | One Streamlit page (`app.py`); no multi-page nav, no background services, no separate backend | PASS |
| II. Small, Focused Changes | Plan splits work into independently small modules (`app.py`, `scoring.py`, `parsing.py`, `groq_client.py`); implementation tasks will be scoped accordingly | PASS |
| III. Test-Covered Logic | The JSON response parser (`parsing.py`) and score calculation (`scoring.py`) are isolated from Streamlit/network code specifically so pytest can cover them | PASS |
| IV. Configuration Over Hardcoding | Six-criteria rubric, including weights, lives in `rubric.yaml`; no scores/weights/thresholds embedded in code | PASS |
| V. Secrets Stay in the Environment | `groq_client.py` reads `GROQ_API_KEY` via `os.environ`; `.env` is gitignored; no key ever hardcoded | PASS |
| VI. Clarify Before Guessing | Spec's Assumptions section documents every default chosen (e.g., weighted overall score once weights were provided); no open ambiguities carried into design | PASS |

No violations — Complexity Tracking table is not needed.

## Project Structure

### Documentation (this feature)

```text
specs/001-ticket-readiness-checker/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
app.py                   # Streamlit entry point: input area, trigger button, results display
scoring.py                # Computes per-criterion + weighted overall score by calling
                           # groq_client against the rubric; testable score-calculation logic
parsing.py                 # Parses and validates the Groq JSON response into structured
                           # criterion scores + missing-items data
groq_client.py             # Thin wrapper around the Groq API call; requests a JSON response;
                           # reads GROQ_API_KEY from env
rubric.yaml                 # Six-criteria scoring rubric with per-criterion weights and
                           # missing-item guidance (no database — this is the only config store)
tests/
└── unit/
    ├── test_parsing.py   # Unit tests for the JSON response parser
    └── test_scoring.py   # Unit tests for the score calculation (incl. weighting)
requirements.txt
.env.example               # Documents GROQ_API_KEY as a placeholder; real values never committed
.gitignore                  # Excludes .env and other local secrets
```

**Structure Decision**: Single flat Python project at the repo root (no `src/` nesting,
no frontend/backend split, no auth layer) — the smallest structure that satisfies
Constitution Principle I (single-page simplicity) and the user's explicit "no database,
no auth" constraint. Scoring and parsing logic are isolated into their own modules,
separate from the Streamlit UI (`app.py`) and the network call (`groq_client.py`),
specifically so the JSON parser and score calculation can be unit-tested per Principle
III without a Streamlit runtime or live network access.

## Complexity Tracking

> No Constitution Check violations — this section is intentionally empty.

**Post-Phase 1 re-check**: data-model.md, contracts/, and quickstart.md (below)
introduce no new dependencies, pages, database, or auth, and keep the rubric (with its
weights) in `rubric.yaml` and the secret in the environment. All six gates above still
PASS after design.
