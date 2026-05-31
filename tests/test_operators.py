import pytest

from app.errors import ValidationError
from app.operators import apply_step, validate_step


def test_filter_keeps_matching_rows():
    rows = [{"x": 1}, {"x": 2}, {"x": 3}]
    out = apply_step(rows, {"type": "filter", "config": {"column": "x", "op": "gte", "value": 2}})
    assert out == [{"x": 2}, {"x": 3}]


def test_filter_validates_op():
    with pytest.raises(ValidationError):
        validate_step({"type": "filter", "config": {"column": "x", "op": "between", "value": 2}})


def test_select_projects_and_renames():
    rows = [{"a": 1, "b": 2, "c": 3}]
    out = apply_step(rows, {"type": "select", "config": {"columns": ["a", "b"], "rename": {"b": "bee"}}})
    assert out == [{"a": 1, "bee": 2}]


def test_select_requires_columns():
    with pytest.raises(ValidationError):
        validate_step({"type": "select", "config": {"columns": []}})


def test_unknown_operator_raises():
    with pytest.raises(ValidationError):
        apply_step([], {"type": "nope", "config": {}})
