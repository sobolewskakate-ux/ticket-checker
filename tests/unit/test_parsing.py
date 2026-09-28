"""Unit tests for parsing.parse_response()."""

import json

import pytest

from parsing import ParsingError, parse_response
from scoring import REQUIRED_CRITERION_KEYS

EXPECTED_KEYS = list(REQUIRED_CRITERION_KEYS)


def _ok_response(scores, missing_items=None):
    missing_items = missing_items or {}
    return json.dumps(
        {
            "status": "ok",
            "criteria": {
                key: {"score": scores[key], "missing_items": missing_items.get(key, [])}
                for key in EXPECTED_KEYS
            },
        }
    )


def test_parse_response_ok_returns_six_criterion_scores():
    scores = {key: 80 for key in EXPECTED_KEYS}
    raw = _ok_response(scores)

    outcome = parse_response(raw, EXPECTED_KEYS)

    assert outcome.status == "ok"
    assert outcome.assessment is not None
    result_keys = {cs.key for cs in outcome.assessment.criterion_scores}
    assert result_keys == set(EXPECTED_KEYS)
    for cs in outcome.assessment.criterion_scores:
        assert cs.score == 80


def test_parse_response_invalid_json_raises_parsing_error():
    with pytest.raises(ParsingError):
        parse_response("not json", EXPECTED_KEYS)


def test_parse_response_missing_criterion_key_raises_parsing_error():
    raw_dict = json.loads(_ok_response({key: 80 for key in EXPECTED_KEYS}))
    del raw_dict["criteria"][EXPECTED_KEYS[0]]

    with pytest.raises(ParsingError):
        parse_response(json.dumps(raw_dict), EXPECTED_KEYS)


@pytest.mark.parametrize("bad_score", [-1, 101, "not-a-number", None])
def test_parse_response_out_of_range_or_non_numeric_score_raises_parsing_error(bad_score):
    raw_dict = {
        "status": "ok",
        "criteria": {key: {"score": 80, "missing_items": []} for key in EXPECTED_KEYS},
    }
    raw_dict["criteria"][EXPECTED_KEYS[0]]["score"] = bad_score

    with pytest.raises(ParsingError):
        parse_response(json.dumps(raw_dict), EXPECTED_KEYS)


def test_parse_response_too_short_returns_guidance_only():
    raw = json.dumps({"status": "too_short", "guidance_message": "Please add more detail."})

    outcome = parse_response(raw, EXPECTED_KEYS)

    assert outcome.status == "too_short"
    assert outcome.assessment is None
    assert outcome.guidance_message == "Please add more detail."


def test_parse_response_too_long_returns_guidance_and_split():
    raw = json.dumps(
        {
            "status": "too_long",
            "guidance_message": "This looks like multiple tickets.",
            "proposed_split": ["Ticket A text", "Ticket B text"],
        }
    )

    outcome = parse_response(raw, EXPECTED_KEYS)

    assert outcome.status == "too_long"
    assert outcome.assessment is None
    assert outcome.guidance_message == "This looks like multiple tickets."
    assert outcome.proposed_split == ["Ticket A text", "Ticket B text"]


def test_parse_response_forces_empty_missing_items_when_score_is_50_or_above():
    key = EXPECTED_KEYS[0]
    scores = {k: 80 for k in EXPECTED_KEYS}
    raw = _ok_response(scores, {key: ["This should be dropped"]})

    outcome = parse_response(raw, EXPECTED_KEYS)

    target = next(cs for cs in outcome.assessment.criterion_scores if cs.key == key)
    assert target.missing_items == []


def test_parse_response_preserves_missing_items_when_score_is_below_50():
    key = EXPECTED_KEYS[0]
    scores = {k: 80 for k in EXPECTED_KEYS}
    scores[key] = 20
    raw = _ok_response(scores, {key: ["No pass/fail conditions stated"]})

    outcome = parse_response(raw, EXPECTED_KEYS)

    target = next(cs for cs in outcome.assessment.criterion_scores if cs.key == key)
    assert target.missing_items == ["No pass/fail conditions stated"]
