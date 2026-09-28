# Contract: `rubric.yaml`

The project's one config interface: the file a maintainer edits to change scoring
behavior (criteria descriptions and weights) without touching code (Constitution
Principle IV). `scoring.py` and `parsing.py` both depend on this exact shape. Lives at
the repository root as `rubric.yaml` (per this round's explicit instruction).

## Schema

```yaml
criteria:
  - key: goal                    # one of the six fixed keys below
    label: "Goal"
    weight: 1.0                  # > 0; need not sum to 1 or 100 across all six entries
    description: >
      What this criterion evaluates, written as guidance for the scoring model.
    missing_item_examples:       # optional
      - "No clear statement of what the ticket is trying to achieve"

  - key: acceptance_criteria
    label: "Acceptance Criteria"
    weight: 1.5
    description: >
      ...
    missing_item_examples:
      - "No pass/fail conditions stated"

  # ... exactly six entries total, one per key below
```

**Required top-level key**: `criteria` — a list.

**Required `key` values** (exactly these six, each appearing exactly once):
`goal`, `acceptance_criteria`, `scope`, `dependencies`, `test_plan`, `constraints`.

**Required fields per entry**: `key` (str), `label` (str), `description` (str),
`weight` (number, > 0).

**Optional fields per entry**: `missing_item_examples` (list of str).

## Weight semantics

`scoring.py` normalizes weights before computing the overall score:
`normalized_weight[i] = weight[i] / sum(all six weights)`. The overall score is
`round(sum(criterion_score[i] * normalized_weight[i] for i in 1..6))`. This means the
rubric author can use any positive scale (e.g., `1`-`5`, or `10`-`30`) and does not need
the weights to sum to any particular total.

## Failure behavior

If `rubric.yaml` is missing, malformed YAML, missing the `criteria` key, missing/invalid
`weight` on any entry, or does not contain exactly the six required `key` values — the
app MUST fail fast at startup (or on first evaluation attempt) with a clear error
identifying the problem, rather than scoring against a partial or guessed rubric. Covered
by unit tests (rubric-loading tests alongside `tests/unit/test_scoring.py`).

## Consumers

- `scoring.py` reads this file to build the prompt sent to the Groq API (criterion
  `label` + `description` become scoring instructions) and to compute the weighted
  `overall_score` from the returned per-criterion scores.
- `parsing.py` uses the six `key` values as the authoritative set of criteria expected in
  the Groq API's JSON response.
