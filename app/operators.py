"""Transform operators for the pipeline engine.

A pipeline step looks like ``{"type": "...", "config": {...}}``. The engine
calls ``validate_step`` when a pipeline is created and ``apply_step`` when it
runs. Both look at ``step["type"]`` to decide what to do.
"""

from __future__ import annotations

from .errors import ValidationError

# Operator types the API advertises on GET /operators.
OPERATOR_TYPES = ["filter", "select"]


def validate_step(step):
    """Raise ValidationError if a step's config can't be applied."""
    op = step.get("type")
    config = step.get("config", {})

    if op == "filter":
        if not isinstance(config.get("column"), str):
            raise ValidationError('filter: "column" must be a string')
        if config.get("op") not in ("eq", "neq", "gt", "gte", "lt", "lte"):
            raise ValidationError('filter: "op" must be one of eq, neq, gt, gte, lt, lte')
        if "value" not in config:
            raise ValidationError('filter: "value" is required')

    elif op == "select":
        columns = config.get("columns")
        if not isinstance(columns, list) or not columns:
            raise ValidationError('select: "columns" must be a non-empty list')
        for c in columns:
            if not isinstance(c, str):
                raise ValidationError('select: every entry in "columns" must be a string')
        if config.get("rename") is not None and not isinstance(config.get("rename"), dict):
            raise ValidationError('select: "rename" must be an object')

    else:
        raise ValidationError(f'Unknown operator type: "{op}"')


def apply_step(rows, step):
    """Apply a single step to ``rows`` and return the resulting rows."""
    op = step.get("type")
    config = step.get("config", {})

    if op == "filter":
        column = config["column"]
        comparison = config["op"]
        value = config["value"]
        out = []
        for row in rows:
            cell = row.get(column)
            if comparison == "eq":
                keep = cell == value
            elif comparison == "neq":
                keep = cell != value
            elif comparison == "gt":
                keep = cell > value
            elif comparison == "gte":
                keep = cell >= value
            elif comparison == "lt":
                keep = cell < value
            elif comparison == "lte":
                keep = cell <= value
            else:
                raise ValidationError(f'filter: bad op "{comparison}"')
            if keep:
                out.append(row)
        return out

    elif op == "select":
        columns = config["columns"]
        rename = config.get("rename") or {}
        out = []
        for row in rows:
            new_row = {}
            for c in columns:
                if c in rename:
                    new_row[rename[c]] = row.get(c)
                else:
                    new_row[c] = row.get(c)
            out.append(new_row)
        return out

    else:
        raise ValidationError(f'Unknown operator type: "{op}"')
