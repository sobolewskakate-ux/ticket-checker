# Quickstart: Ticket Readiness Checker

Validates the feature end-to-end once implemented. See [data-model.md](./data-model.md)
and [contracts/](./contracts/) for the underlying structures.

## Prerequisites

- Python 3.12
- A Groq API key

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configure

```bash
export GROQ_API_KEY="your-key-here"
```

Never write the real key into `.env` and commit it — `.env` is gitignored;
`.env.example` documents the variable name only, with a placeholder value. There is no
database and no login to configure.

## Run

```bash
streamlit run app.py
```

Opens the app in a browser at the default Streamlit local URL.

## Validate User Story 1 — Score a pasted ticket (weighted overall score)

1. Paste a well-specified ticket, e.g.:

   > Goal: Add a "forgot password" link to the login page.
   > Acceptance criteria: Clicking the link navigates to /reset-password; entering a
   > registered email sends a reset link; entering an unregistered email shows a
   > generic "if this email exists..." message.
   > Scope: Login page and reset-password flow only; no changes to signup.
   > Dependencies: Requires the existing email-sending service.
   > Test plan: Unit tests for the reset-request handler; manual test of the email
   > delivery in staging.
   > Constraints: Must not reveal whether an email is registered.

2. Click the check button.
3. **Expect**: all six criteria display a score, plus an overall score computed from
   `rubric.yaml`'s per-criterion weights (see contracts/rubric-config.md), within ~15
   seconds (SC-001). Most/all criteria should score 50 or above.

## Validate User Story 2 — See what's missing

1. Paste a vague-but-complete ticket, e.g.: `Fix the login bug on the account page.`
2. Click the check button.
3. **Expect**: most or all criteria score below 50, and each of those criteria shows a
   list of specific missing items. Confirm no missing-items list appears under any
   criterion scoring 50 or above.

## Validate User Story 3 — Revise and re-check

1. Starting from the vague ticket above, edit the pasted text to add a goal statement
   and acceptance criteria.
2. Click the check button again.
3. **Expect**: the results update in place — old scores/missing-items are fully replaced,
   and the criteria you improved now score higher than before.

## Validate FR-013 — Too-short input

1. Paste a single word, e.g. `Bug.`
2. Click the check button.
3. **Expect**: no scores are shown. Instead, a message explains the expected ticket
   format and names all six criteria (goal, acceptance criteria, scope, dependencies,
   test plan, constraints), prompting for a more elaborate description.

## Validate FR-014 — Too-long / multi-ticket input

1. Paste a long block of text that plausibly bundles two or three unrelated tickets
   (e.g., a bug fix, an unrelated feature request, and a chunk of log output).
2. Click the check button.
3. **Expect**: no single combined score is shown. Instead, the app proposes a split into
   separate tickets and suggests copying each one to re-run the check individually.

## Validate error handling

1. Click the check button with the input left empty.
   **Expect**: a prompt to enter ticket text; no score is shown.
2. Temporarily unset `GROQ_API_KEY` and restart the app, then run a check.
   **Expect**: a clear, actionable error message; no partial or fabricated score.

## Run unit tests

```bash
pytest tests/unit -v
```

**Expect**: all tests in `test_parsing.py` (JSON response parsing, including
`status: ok / too_short / too_long` handling) and `test_scoring.py` (weighted score
calculation via `compute_overall_score`, rubric loading/validation) pass — covering
normal cases and the edge cases in
[contracts/scoring-interface.md](./contracts/scoring-interface.md) (malformed LLM
response, out-of-range scores, missing criteria, missing/invalid weights, the
`missing_items` vs. `score >= 50` rule).
