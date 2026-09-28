"""Unit tests for scoring.load_rubric() and scoring.compute_overall_score()."""

import yaml

import pytest

from scoring import (
    REQUIRED_CRITERION_KEYS,
    CriterionScore,
    RubricConfigError,
    RubricCriterion,
    compute_overall_score,
    load_rubric,
)


def _write_rubric(tmp_path, criteria):
    path = tmp_path / "rubric.yaml"
    path.write_text(yaml.safe_dump({"criteria": criteria}))
    return str(path)


def _valid_criteria():
    return [
        {
            "key": key,
            "label": key.replace("_", " ").title(),
            "description": f"Evaluates {key}.",
            "weight": 1.0,
        }
        for key in REQUIRED_CRITERION_KEYS
    ]


def test_load_rubric_valid_file_returns_six_criteria(tmp_path):
    path = _write_rubric(tmp_path, _valid_criteria())

    criteria = load_rubric(path)

    assert {c.key for c in criteria} == set(REQUIRED_CRITERION_KEYS)
    assert all(isinstance(c, RubricCriterion) for c in criteria)


def test_load_rubric_missing_file_raises_rubric_config_error(tmp_path):
    with pytest.raises(RubricConfigError):
        load_rubric(str(tmp_path / "does-not-exist.yaml"))


def test_load_rubric_missing_criteria_key_raises_rubric_config_error(tmp_path):
    path = tmp_path / "rubric.yaml"
    path.write_text(yaml.safe_dump({"not_criteria": []}))

    with pytest.raises(RubricConfigError):
        load_rubric(str(path))


def test_load_rubric_incomplete_criteria_raises_rubric_config_error(tmp_path):
    criteria = _valid_criteria()[:-1]
    path = _write_rubric(tmp_path, criteria)

    with pytest.raises(RubricConfigError):
        load_rubric(path)


def test_load_rubric_non_positive_weight_raises_rubric_config_error(tmp_path):
    criteria = _valid_criteria()
    criteria[0]["weight"] = 0
    path = _write_rubric(tmp_path, criteria)

    with pytest.raises(RubricConfigError):
        load_rubric(path)


def test_compute_overall_score_weighted_average_matches_hand_calculation():
    rubric = [
        RubricCriterion(key="goal", label="Goal", description="d", weight=1.0),
        RubricCriterion(key="acceptance_criteria", label="AC", description="d", weight=3.0),
    ]
    scores = [
        CriterionScore(key="goal", score=100, missing_items=[]),
        CriterionScore(key="acceptance_criteria", score=0, missing_items=["x"]),
    ]

    # normalized weights: goal=0.25, acceptance_criteria=0.75
    # weighted sum = 100*0.25 + 0*0.75 = 25
    assert compute_overall_score(scores, rubric) == 25


def test_compute_overall_score_rounds_to_nearest_integer():
    rubric = [
        RubricCriterion(key="goal", label="Goal", description="d", weight=1.0),
        RubricCriterion(key="acceptance_criteria", label="AC", description="d", weight=1.0),
        RubricCriterion(key="scope", label="Scope", description="d", weight=1.0),
    ]
    scores = [
        CriterionScore(key="goal", score=100, missing_items=[]),
        CriterionScore(key="acceptance_criteria", score=100, missing_items=[]),
        CriterionScore(key="scope", score=99, missing_items=[]),
    ]

    # average = (100 + 100 + 99) / 3 = 99.6666... -> rounds to 100
    assert compute_overall_score(scores, rubric) == 100
