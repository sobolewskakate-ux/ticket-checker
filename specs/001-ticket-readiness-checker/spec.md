# Feature Specification: Ticket Readiness Checker

**Feature Branch**: `001-ticket-readiness-checker`

**Created**: 2026-09-28

**Status**: Draft

**Input**: User description: "Build a small Streamlit app called Ticket Readiness Checker. A user pastes a software ticket, and the app scores it from 0 to 100 on six criteria: goal, acceptance criteria, scope, dependencies, test plan, and constraints. For every criterion below 50, the app lists what is missing. The users are engineering managers and developers who delegate tickets to AI coding agents. Out of scope: Jira or Linear integration, login, and storage."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Score a pasted ticket (Priority: P1)

An engineering manager or developer pastes the text of a software ticket they are about to
hand to an AI coding agent. The app evaluates the ticket and returns a score from 0-100 for
each of six criteria — goal, acceptance criteria, scope, dependencies, test plan, and
constraints — plus an overall readiness score.

**Why this priority**: This is the core value of the tool. Without a score, there is no
product; every other capability builds on this one.

**Independent Test**: Paste any ticket text and trigger a check. Delivers value on its own by
telling the user, at a glance, how ready the ticket is before it's handed off.

**Acceptance Scenarios**:

1. **Given** a blank input area, **When** the user pastes ticket text and runs the check,
   **Then** the app displays a score from 0-100 for each of the six criteria and an overall
   score.
2. **Given** a ticket that clearly states its goal, acceptance criteria, scope, dependencies,
   test plan, and constraints, **When** checked, **Then** all six criteria score 50 or above.
3. **Given** a ticket that is one vague but complete sentence (e.g., "Fix the login bug."),
   **When** checked, **Then** most or all criteria score below 50.

---

### User Story 2 - See what's missing for weak criteria (Priority: P1)

For any criterion that scores below 50, the user sees a list of the specific things missing
from the ticket for that criterion, so they know exactly what to add before delegating the
ticket to an AI coding agent.

**Why this priority**: A bare score tells the user *that* a ticket is weak but not *why*.
The missing-items list is what makes the score actionable, so it ships with the first
release alongside scoring.

**Independent Test**: Check a ticket with at least one criterion below 50 and confirm a
missing-items list appears under that criterion, and only that criterion.

**Acceptance Scenarios**:

1. **Given** a checked ticket where "acceptance criteria" scores below 50, **When** results
   are displayed, **Then** the app lists the specific items missing for acceptance criteria
   (e.g., no pass/fail conditions stated).
2. **Given** a checked ticket where a criterion scores 50 or above, **When** results are
   displayed, **Then** no missing-items list is shown for that criterion.
3. **Given** a checked ticket where all six criteria score 50 or above, **When** results are
   displayed, **Then** no missing-items lists are shown anywhere.

---

### User Story 3 - Revise and re-check a ticket (Priority: P2)

Having seen which criteria are weak and what's missing, the user edits the pasted ticket text
(in place or by pasting a revised version) and re-runs the check to confirm the ticket is now
ready.

**Why this priority**: This closes the loop that makes the tool useful for actually improving
tickets, not just diagnosing them, but the tool is already usable without it if a user simply
re-opens the app for each attempt.

**Independent Test**: After an initial check, change the pasted text and run the check again;
confirm scores update to reflect the new text with no leftover state from the previous check.

**Acceptance Scenarios**:

1. **Given** a completed check with a low score on some criteria, **When** the user edits the
   ticket text and re-runs the check, **Then** the displayed scores and missing-items lists
   are replaced with results for the new text.

---

### Edge Cases

- What happens when the user runs a check with no ticket text pasted? The app MUST prompt the
  user to enter ticket text instead of returning a score.
- What happens when a ticket already scores 100 on a criterion? No missing items are shown for
  that criterion.
- What happens when the scoring service is unavailable or the request fails? The app MUST show
  a clear, actionable error message and MUST NOT display a partial or fabricated score.
- How does the app handle extremely short input (e.g., a single word)? The app MUST NOT
  attempt to score it. Instead it MUST instruct the user about the expected ticket format —
  naming the six criteria (goal, acceptance criteria, scope, dependencies, test plan,
  constraints) — and ask them to provide a more elaborate ticket description.
- How does the app handle very long pasted text (e.g., a multi-page ticket with embedded
  logs)? The app MUST NOT score the whole block as a single ticket. Instead it MUST propose
  splitting the text into multiple smaller tickets, present the proposed split to the user,
  and suggest the user copy the individual proposed tickets and re-run the check separately
  for each one.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The app MUST provide a single text input area where a user pastes the full text
  of a software ticket.
- **FR-002**: The app MUST let the user trigger an evaluation of the pasted ticket on demand
  (e.g., via a button).
- **FR-003**: The app MUST score the pasted ticket from 0 to 100 on each of six criteria:
  goal, acceptance criteria, scope, dependencies, test plan, and constraints — except when
  the input is too short (FR-013) or too long (FR-014) to score directly.
- **FR-004**: The app MUST display all six criterion scores together with an overall
  readiness score after each evaluation.
- **FR-005**: For every criterion scoring below 50, the app MUST list the specific
  information or elements missing from the ticket for that criterion.
- **FR-006**: The app MUST NOT display a missing-items list for a criterion scoring 50 or
  above.
- **FR-007**: The app MUST allow the user to change the pasted ticket text and re-run the
  evaluation, replacing the previous results.
- **FR-008**: The app MUST indicate to the user when an evaluation is in progress.
- **FR-009**: The app MUST show a clear, actionable message when an evaluation cannot be
  completed (e.g., empty input, evaluation failure) instead of failing silently or showing a
  blank result.
- **FR-010**: The app MUST NOT require the user to create an account or log in.
- **FR-011**: The app MUST NOT persist pasted ticket text, scores, or missing-items lists
  beyond the current session.
- **FR-012**: The app MUST NOT integrate with Jira, Linear, or any other issue-tracking
  system for importing or exporting tickets.
- **FR-013**: When the pasted text is too brief to contain identifiable content for any of
  the six criteria (e.g., a single word or a sentence fragment), the app MUST NOT return
  criterion scores. Instead it MUST explain the expected ticket format — naming the six
  criteria — and prompt the user to paste a more elaborate ticket description.
- **FR-014**: When the pasted text is long enough to plausibly contain more than one
  distinct ticket (e.g., a multi-page ticket with embedded logs), the app MUST NOT score it
  as a single ticket. Instead it MUST propose a split into multiple smaller tickets, show
  the user the proposed split, and suggest the user copy each proposed ticket and re-run the
  check individually for each one.

### Key Entities

- **Ticket Submission**: The raw text of one software ticket pasted by the user for a single
  evaluation. Exists only for the duration of that evaluation/session; not stored afterward.
- **Criterion Score**: The 0-100 score and (when below 50) the list of missing items for one
  of the six criteria — goal, acceptance criteria, scope, dependencies, test plan,
  constraints — produced for a given Ticket Submission.
- **Readiness Assessment**: The set of six Criterion Scores plus the overall readiness score
  produced for one Ticket Submission.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can go from pasting a ticket to seeing all six criterion scores and an
  overall score in under 15 seconds.
- **SC-002**: For any criterion scoring below 50, the user can identify at least one concrete,
  specific missing item without needing to guess what the score means.
- **SC-003**: A user with no prior instructions can complete a first ticket evaluation within
  1 minute of opening the app, with no account setup or configuration required.
- **SC-004**: When a user revises a ticket to address a listed missing item and re-checks it,
  the corresponding criterion's score increases.

## Assumptions

- The overall readiness score is the average of the six criterion scores unless a more
  specific aggregation is requested later; this is a reasonable default that keeps the score
  simple to explain.
- The tool evaluates one pasted ticket at a time; batch evaluation of multiple tickets is out
  of scope for this feature.
- "No storage" means ticket text, scores, and missing-items lists are not persisted beyond the
  current browser session — they are not written to a database, file, or external service.
- "No login" means the tool is used anonymously with no user accounts, profiles, or
  per-user history.
- Users paste ticket text manually; no automated import from Jira, Linear, or other systems is
  provided (confirmed out of scope by the user).
- Ticket text is assumed to be in English. There is no hard character limit on input, but
  text judged too short (FR-013) or long enough to plausibly hold multiple tickets (FR-014)
  is redirected to guidance rather than scored directly; typical single-ticket length is a
  few sentences to a few paragraphs.
- "Too short to score" and "long enough to plausibly contain multiple tickets" are judged on
  content, not a fixed word/character count — the exact boundary is left to implementation
  and is expected to rely on the same evaluation step used for scoring.
