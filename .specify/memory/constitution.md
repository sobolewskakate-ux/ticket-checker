<!--
Sync Impact Report
- Version change: [none] → 1.0.0 (initial ratification)
- Modified principles: n/a (all principles newly defined)
- Added sections:
  - Core Principles: I. Single-Page Simplicity, II. Small, Focused Changes,
    III. Test-Covered Logic, IV. Configuration Over Hardcoding,
    V. Secrets Stay in the Environment, VI. Clarify Before Guessing
  - Technology Stack (Section 2)
  - Quality Gates (Section 3)
  - Governance
- Removed sections: none (initial creation from template)
- Deferred items: TODO(RATIFICATION_DATE) — original adoption date not supplied by user;
  set to today's date when the user confirms the true ratification date.
- Templates requiring follow-up: none checked in this run (constitution command is
  scoped to this file only; dependent templates read it at runtime).
-->

# Ticket Checker Constitution

## Core Principles

### I. Single-Page Simplicity
The application MUST remain a single-page Streamlit app. New functionality is added by
extending the existing page's flow, not by introducing multi-page navigation, background
services, or a separate backend. If a feature seems to require more than one page or a
persistent server process, treat that as a signal to simplify the feature, not the
constitution.
**Rationale**: The project's value is a small, easy-to-run tool; multi-page or
multi-service architecture adds operational and cognitive overhead disproportionate to
its purpose.

### II. Small, Focused Changes
Every change (commit, PR, or agent-driven edit) MUST do one thing and MUST NOT bundle
unrelated refactors, formatting sweeps, or "while I'm here" cleanups. A bug fix does not
require surrounding cleanup; a one-shot script does not need a reusable abstraction.
**Rationale**: Small diffs are the primary defense against regressions in a project with
a small test surface and a single maintainer reviewing changes.

### III. Test-Covered Logic
Scoring logic and parsing logic MUST have pytest unit tests. Tests MUST cover the
normal case plus the edge cases that matter for correctness (e.g., malformed input,
boundary scores, missing rubric fields). UI code (Streamlit widgets/layout) is exempt
from this requirement, but any non-trivial logic extracted from it is not.
**Rationale**: Scoring and parsing are the parts of the app where a silent bug produces
a wrong answer nobody notices; UI code fails visibly and is cheap to eyeball-check.

### IV. Configuration Over Hardcoding
The scoring rubric MUST live in a config file (e.g., YAML/JSON/TOML), never as literal
values embedded in application or test code. Code reads the rubric from config; it does
not encode rubric values, weights, or thresholds directly.
**Rationale**: Keeping the rubric in config lets it be reviewed, changed, and tested
independently of the code that applies it, and prevents scoring logic and scoring
*values* from silently drifting apart.

### V. Secrets Stay in the Environment
`GROQ_API_KEY` (and any other credential) MUST be read from an environment variable at
runtime. Keys, tokens, and `.env` files containing real secrets MUST NOT be committed to
version control. Example/template env files MUST use placeholder values only.
**Rationale**: This is a small app likely to be shared or open-sourced; a committed key
is a leak the moment the repo is pushed anywhere.

### VI. Clarify Before Guessing
When a requirement, rubric detail, or scope boundary is ambiguous, the developer (human
or agent) MUST ask rather than silently choose an interpretation and proceed.
**Rationale**: Guessing on an ambiguous requirement in a small codebase is more
expensive to unwind than a short clarifying question, and silent assumptions compound
quietly in scoring logic.

## Technology Stack

- **Language/runtime**: Python 3.12.
- **UI framework**: Streamlit, single page.
- **LLM provider**: Groq API, accessed only via the `GROQ_API_KEY` environment
  variable (see Principle V).
- **Testing**: pytest, covering scoring and parsing logic (see Principle III).
- **Rubric storage**: a dedicated config file, not Python source (see Principle IV).

Introducing a different language runtime, UI framework, LLM provider, or test
framework is a stack change and MUST be treated as a constitution amendment, not a
routine code change.

## Quality Gates

- A change that touches scoring or parsing logic MUST include or update the
  corresponding pytest tests in the same change.
- A change MUST NOT introduce a hardcoded rubric value; reviewers MUST reject any diff
  that adds scoring thresholds/weights directly in code instead of the config file.
- A change MUST NOT introduce a literal API key, token, or secret in code, tests,
  fixtures, or commit history; reviewers MUST check for this before merging.
- Before implementing against an ambiguous or underspecified requirement, the
  ambiguity MUST be raised as a question rather than resolved by assumption.

## Governance

This constitution supersedes ad hoc practice for this project. Any change to these
principles, the technology stack, or the quality gates is a constitution amendment and
MUST be made through the `/speckit-constitution` command so the version, dates, and
Sync Impact Report stay consistent.

**Amendment procedure**: propose the change, update this file (principles, affected
sections, and Governance), bump `CONSTITUTION_VERSION` per the versioning policy below,
and record the change in the Sync Impact Report at the top of this file.

**Versioning policy** (semantic versioning for governance):
- **MAJOR**: backward-incompatible principle removal or redefinition (e.g., dropping
  the single-page constraint, allowing hardcoded secrets).
- **MINOR**: a new principle or materially expanded guidance (e.g., adding a new
  quality gate).
- **PATCH**: wording clarifications and non-semantic fixes.

**Compliance review**: any PR or agent-driven change SHOULD be checked against the
Quality Gates above before merge. Complexity that conflicts with Principle I or II
MUST be justified in the change description or simplified.

**Version**: 1.0.0 | **Ratified**: TODO(RATIFICATION_DATE): original adoption date not
provided — confirm with user | **Last Amended**: 2026-09-28
