# Contract: `scoring.py` / `parsing.py` / `groq_client.py` interfaces

Internal module contracts — what the pytest unit tests (JSON parser + score calculation,
per this round's explicit instruction and Constitution Principle III) test against, and
what `app.py` calls.

## `groq_client.py`

```python
def get_completion(prompt: str) -> str:
    """
    Calls the Groq API with `prompt`, requesting a JSON response
    (response_format={"type": "json_object"}), and returns the raw response text.
    Reads GROQ_API_KEY (required) and GROQ_MODEL (optional, has a default) from
    the environment. Never accepts an API key as a parameter or default value —
    env var only (Constitution Principle V).

    Raises ScoringServiceError on any failure: missing/invalid API key, timeout,
    rate limit, or non-2xx response.
    """
```

## `parsing.py`

```python
def parse_response(raw_text: str, expected_keys: list[str]) -> EvaluationOutcome:
    """
    Parses `raw_text` (expected to be a JSON object with a top-level "status"
    field: "ok" | "too_short" | "too_long") into an EvaluationOutcome.

    When status == "ok": requires a "criteria" object/list keyed by each entry
    in `expected_keys`, each with a numeric "score" and a "missing_items" list.
    When status == "too_short": requires a "guidance_message" string.
    When status == "too_long": requires a "guidance_message" string and a
    "proposed_split" list of strings.

    Raises ParsingError if:
      - raw_text is not valid JSON
      - "status" is missing or not one of the three known values
      - (status == "ok") any expected key is missing, or a score is missing,
        non-numeric, or outside [0, 100]
      - (status == "too_short" / "too_long") the required guidance fields are
        missing or empty

    Enforces: for status == "ok", missing_items is forced to [] whenever
    score >= 50, regardless of what the raw response contained (FR-006 is
    authoritative here).
    """
```

## `scoring.py`

```python
def load_rubric(path: str = "rubric.yaml") -> list[RubricCriterion]:
    """
    Loads and validates rubric.yaml per contracts/rubric-config.md, including
    the per-criterion weight field. Raises RubricConfigError if the file is
    missing, malformed, or does not define exactly the six required criteria
    with positive weights.
    """

def compute_overall_score(criterion_scores: list[CriterionScore], rubric: list[RubricCriterion]) -> int:
    """
    Computes the weighted overall score: normalizes rubric weights (each
    weight / sum of all weights) and returns
    round(sum(score_i * normalized_weight_i)), an int in [0, 100].
    Pure function — no network calls — directly unit-testable
    ("pytest for ... score calculation").
    """

def score_ticket(ticket_text: str, rubric: list[RubricCriterion]) -> EvaluationOutcome:
    """
    Builds a prompt from `ticket_text` and `rubric` (including weights and
    descriptions), calls groq_client.get_completion(), parses the result via
    parsing.parse_response(), and — when status == "ok" — computes
    ReadinessAssessment.overall_score via compute_overall_score().

    Raises ScoringServiceError / ParsingError (propagated, not swallowed) so
    app.py can show an actionable error per FR-009.
    """
```

## `app.py` (UI contract, not unit-tested — manually verified via quickstart.md)

- Renders a text area for pasting a ticket (FR-001).
- Renders a button that calls `scoring.score_ticket(...)` (FR-002).
- While the call is in flight, shows a loading indicator (FR-008).
- On `EvaluationOutcome.status == "ok"`: renders all six `CriterionScore` entries (score +
  missing items when `score < 50`) and the weighted `overall_score` (FR-003, FR-004,
  FR-005, FR-006).
- On `status == "too_short"`: renders `guidance_message` (format guidance naming the six
  criteria) instead of any scores (FR-013).
- On `status == "too_long"`: renders `guidance_message` and the `proposed_split` list,
  suggesting the user copy each proposed ticket and re-run individually (FR-014).
- On `RubricConfigError`, `ScoringServiceError`, or `ParsingError`, renders
  `st.error(...)` with the exception's message instead of any partial result (FR-009).
- On empty/whitespace-only ticket text, prompts the user to enter text instead of calling
  `scoring.score_ticket(...)` at all (Edge Cases in spec.md).
