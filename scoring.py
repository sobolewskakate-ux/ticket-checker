"""Rubric loading and score calculation for the Ticket Readiness Checker."""

from __future__ import annotations

from dataclasses import dataclass, field

import yaml

REQUIRED_CRITERION_KEYS = (
    "goal",
    "acceptance_criteria",
    "scope",
    "dependencies",
    "test_plan",
    "constraints",
)


class RubricConfigError(Exception):
    """Raised when rubric.yaml is missing, malformed, or incomplete."""


@dataclass(frozen=True)
class RubricCriterion:
    """One entry from rubric.yaml describing a single scoring criterion."""

    key: str
    label: str
    description: str
    weight: float
    missing_item_examples: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CriterionScore:
    """The score and (when below 50) missing items for one criterion."""

    key: str
    score: int
    missing_items: list[str] = field(default_factory=list)


def load_rubric(path: str = "rubric.yaml") -> list[RubricCriterion]:
    """Load and validate rubric.yaml per contracts/rubric-config.md."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    except FileNotFoundError as exc:
        raise RubricConfigError(f"Rubric config not found at '{path}'") from exc
    except yaml.YAMLError as exc:
        raise RubricConfigError(f"Rubric config at '{path}' is not valid YAML: {exc}") from exc

    if not isinstance(raw, dict) or "criteria" not in raw:
        raise RubricConfigError(
            f"Rubric config at '{path}' must be a mapping with a top-level 'criteria' list"
        )

    entries = raw["criteria"]
    if not isinstance(entries, list):
        raise RubricConfigError(f"'criteria' in '{path}' must be a list")

    criteria: list[RubricCriterion] = []
    seen_keys: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise RubricConfigError(f"Each criterion entry in '{path}' must be a mapping")

        key = entry.get("key")
        label = entry.get("label")
        description = entry.get("description")
        weight = entry.get("weight")

        if key not in REQUIRED_CRITERION_KEYS:
            raise RubricConfigError(
                f"Unknown or missing criterion key {key!r} in '{path}'; "
                f"expected one of {REQUIRED_CRITERION_KEYS}"
            )
        if key in seen_keys:
            raise RubricConfigError(f"Duplicate criterion key {key!r} in '{path}'")
        if not isinstance(label, str) or not label.strip():
            raise RubricConfigError(f"Criterion {key!r} in '{path}' must have a non-empty 'label'")
        if not isinstance(description, str) or not description.strip():
            raise RubricConfigError(
                f"Criterion {key!r} in '{path}' must have a non-empty 'description'"
            )
        if not isinstance(weight, (int, float)) or isinstance(weight, bool) or weight <= 0:
            raise RubricConfigError(
                f"Criterion {key!r} in '{path}' must have a numeric 'weight' > 0"
            )

        missing_item_examples = entry.get("missing_item_examples", [])
        if not isinstance(missing_item_examples, list):
            raise RubricConfigError(
                f"Criterion {key!r} in '{path}': 'missing_item_examples' must be a list"
            )

        seen_keys.add(key)
        criteria.append(
            RubricCriterion(
                key=key,
                label=label,
                description=description,
                weight=float(weight),
                missing_item_examples=[str(item) for item in missing_item_examples],
            )
        )

    missing_keys = set(REQUIRED_CRITERION_KEYS) - seen_keys
    if missing_keys:
        raise RubricConfigError(
            f"Rubric config at '{path}' is missing required criteria: {sorted(missing_keys)}"
        )

    return criteria


def compute_overall_score(
    criterion_scores: list[CriterionScore], rubric: list[RubricCriterion]
) -> int:
    """Weighted average of criterion scores using normalized rubric weights."""
    weights_by_key = {c.key: c.weight for c in rubric}
    total_weight = sum(weights_by_key.values())
    if total_weight <= 0:
        raise RubricConfigError("Rubric weights must sum to a positive number")

    weighted_sum = 0.0
    for cs in criterion_scores:
        weight = weights_by_key.get(cs.key)
        if weight is None:
            raise RubricConfigError(f"No rubric weight found for criterion {cs.key!r}")
        weighted_sum += cs.score * (weight / total_weight)

    return round(weighted_sum)


def _build_prompt(ticket_text: str, rubric: list[RubricCriterion]) -> str:
    """Build the scoring prompt sent to the Groq API."""
    criteria_lines = [
        f'- key: "{c.key}"\n  label: "{c.label}"\n  guidance: {c.description}' for c in rubric
    ]
    criteria_block = "\n".join(criteria_lines)
    expected_keys = ", ".join(f'"{c.key}"' for c in rubric)

    return f"""You are evaluating the readiness of a software ticket that will be handed \
to an AI coding agent to implement. Score it against these six criteria:

{criteria_block}

Ticket text:
\"\"\"
{ticket_text}
\"\"\"

First decide exactly one status:
- "too_short": the text is too brief to identify any of the six criteria (e.g. a single \
word or sentence fragment with no real content).
- "too_long": the text plausibly bundles more than one distinct ticket (e.g. multiple \
unrelated requests, or a ticket plus large chunks of unrelated log output).
- "ok": the text is a single ticket that can be scored on its own.

Respond with ONLY a JSON object (no other text, no markdown fences).

If status is "ok", respond with exactly this shape:
{{"status": "ok", "criteria": {{{expected_keys}: {{"score": <int 0-100>, "missing_items": [<string>, ...]}} for each listed key}}}}
Only include items in "missing_items" for a criterion if its score is below 50.

If status is "too_short", respond with:
{{"status": "too_short", "guidance_message": "<explain the expected ticket format, naming all six criteria by label, and ask for a more elaborate description>"}}

If status is "too_long", respond with:
{{"status": "too_long", "guidance_message": "<explain that the text looks like it bundles multiple tickets>", "proposed_split": ["<proposed ticket 1 text>", "<proposed ticket 2 text>", ...]}}
"""


def score_ticket(ticket_text: str, rubric: list[RubricCriterion]):
    """Score a ticket end-to-end: build prompt, call Groq, parse, compute weighted score."""
    from groq_client import get_completion
    from parsing import parse_response

    prompt = _build_prompt(ticket_text, rubric)
    raw_text = get_completion(prompt)
    expected_keys = [c.key for c in rubric]
    outcome = parse_response(raw_text, expected_keys)

    if outcome.status == "ok":
        outcome.assessment.overall_score = compute_overall_score(
            outcome.assessment.criterion_scores, rubric
        )

    return outcome
