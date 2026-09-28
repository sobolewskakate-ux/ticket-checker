"""Parses and validates the Groq API's JSON response into structured results."""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from scoring import CriterionScore

VALID_STATUSES = ("ok", "too_short", "too_long")


class ParsingError(Exception):
    """Raised when the Groq API's response cannot be parsed into a valid outcome."""


@dataclass
class ReadinessAssessment:
    """Six criterion scores plus the (later, weight-computed) overall score."""

    criterion_scores: list[CriterionScore] = field(default_factory=list)
    overall_score: int = 0


@dataclass
class EvaluationOutcome:
    """The top-level result of one ticket check: a score, or guidance."""

    status: str
    assessment: ReadinessAssessment | None = None
    guidance_message: str | None = None
    proposed_split: list[str] | None = None


def parse_response(raw_text: str, expected_keys: list[str]) -> EvaluationOutcome:
    """Parse and validate the Groq API's raw JSON response text."""
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ParsingError(f"Response was not valid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ParsingError("Response JSON must be an object")

    status = data.get("status")
    if status not in VALID_STATUSES:
        raise ParsingError(f"Response 'status' must be one of {VALID_STATUSES}, got {status!r}")

    if status == "ok":
        return _parse_ok(data, expected_keys)
    return _parse_guidance(data, status)


def _parse_ok(data: dict, expected_keys: list[str]) -> EvaluationOutcome:
    criteria = data.get("criteria")
    if not isinstance(criteria, dict):
        raise ParsingError("Response with status 'ok' must include a 'criteria' object")

    missing_keys = [key for key in expected_keys if key not in criteria]
    if missing_keys:
        raise ParsingError(f"Response is missing criteria: {missing_keys}")

    criterion_scores: list[CriterionScore] = []
    for key in expected_keys:
        entry = criteria[key]
        if not isinstance(entry, dict):
            raise ParsingError(f"Criterion {key!r} entry must be an object")

        score = entry.get("score")
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise ParsingError(f"Criterion {key!r} score must be numeric, got {score!r}")
        score = int(score)
        if not 0 <= score <= 100:
            raise ParsingError(f"Criterion {key!r} score must be in [0, 100], got {score}")

        raw_missing_items = entry.get("missing_items", [])
        if not isinstance(raw_missing_items, list):
            raise ParsingError(f"Criterion {key!r} 'missing_items' must be a list")

        # FR-006 is authoritative: never surface missing items for score >= 50,
        # regardless of what the raw response contained.
        missing_items = [] if score >= 50 else [str(item) for item in raw_missing_items]

        criterion_scores.append(CriterionScore(key=key, score=score, missing_items=missing_items))

    return EvaluationOutcome(
        status="ok",
        assessment=ReadinessAssessment(criterion_scores=criterion_scores, overall_score=0),
    )


def _parse_guidance(data: dict, status: str) -> EvaluationOutcome:
    guidance_message = data.get("guidance_message")
    if not isinstance(guidance_message, str) or not guidance_message.strip():
        raise ParsingError(
            f"Response with status {status!r} must include a non-empty 'guidance_message'"
        )

    if status == "too_short":
        return EvaluationOutcome(status=status, guidance_message=guidance_message)

    # status == "too_long"
    proposed_split = data.get("proposed_split")
    if not isinstance(proposed_split, list) or not proposed_split:
        raise ParsingError(
            "Response with status 'too_long' must include a non-empty 'proposed_split' list"
        )

    return EvaluationOutcome(
        status=status,
        guidance_message=guidance_message,
        proposed_split=[str(item) for item in proposed_split],
    )
