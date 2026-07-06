"""JSON (de)serialization для Locator."""

from __future__ import annotations

import json
from typing import Any

from autoui.locators.errors import LocatorError
from autoui.locators.locator import Locator
from autoui.locators.ops import (
    ChildOp,
    FilterOp,
    FilterWhere,
    FindDescendantsOp,
    LocatorOp,
    TakeOp,
    validate_filter_where,
)


def locator_to_dict(locator: Locator) -> dict[str, Any]:
    return {"ops": [_op_to_dict(op) for op in locator.ops]}


def locator_from_dict(data: dict[str, Any]) -> Locator:
    if "find" in data:
        where = validate_filter_where(dict(data["find"]))
        depth = _optional_positive_int(data.get("depth"), "depth")
        limit = _optional_positive_int(data.get("limit"), "limit")
        return Locator.find(depth=depth, limit=limit, **where)
    if "ops" not in data:
        raise LocatorError("Locator dict must contain 'ops' or 'find'")
    ops_data = data["ops"]
    if not isinstance(ops_data, list):
        raise LocatorError("'ops' must be a list")
    return Locator([_op_from_dict(item) for item in ops_data])


def locator_to_json(locator: Locator) -> str:
    return json.dumps(locator_to_dict(locator), ensure_ascii=False)


def locator_from_json(text: str) -> Locator:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LocatorError(f"Invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise LocatorError("Locator JSON root must be an object")
    return locator_from_dict(data)


def _op_to_dict(op: LocatorOp) -> dict[str, Any]:
    if isinstance(op, ChildOp):
        return {"op": "child", "index": op.index}
    if isinstance(op, FindDescendantsOp):
        payload: dict[str, Any] = {"op": "find_descendants", "where": dict(op.where)}
        if op.depth is not None:
            payload["depth"] = op.depth
        if op.limit is not None:
            payload["limit"] = op.limit
        return payload
    if isinstance(op, FilterOp):
        return {"op": "filter", "where": dict(op.where)}
    if isinstance(op, TakeOp):
        return {"op": "take", "index": op.index}
    raise LocatorError(f"Unknown op type: {type(op)!r}")


def _op_from_dict(data: dict[str, Any]) -> LocatorOp:
    if not isinstance(data, dict):
        raise LocatorError(f"Op must be an object, got {type(data)!r}")
    op_name = data.get("op")
    if op_name == "child":
        if "index" not in data:
            raise LocatorError("child op requires 'index'")
        return ChildOp(index=int(data["index"]))
    if op_name == "find_descendants":
        where = _parse_where(data.get("where"))
        depth = _optional_positive_int(data.get("depth"), "depth")
        limit = _optional_positive_int(data.get("limit"), "limit")
        try:
            return FindDescendantsOp(where=where, depth=depth, limit=limit)
        except ValueError as exc:
            raise LocatorError(str(exc)) from exc
    if op_name == "filter":
        where = _parse_where(data.get("where"))
        return FilterOp(where=where)
    if op_name == "take":
        if "index" not in data:
            raise LocatorError("take op requires 'index'")
        return TakeOp(index=int(data["index"]))
    raise LocatorError(f"Unknown op name: {op_name!r}")


def _parse_where(raw: Any) -> FilterWhere:
    if not isinstance(raw, dict):
        raise LocatorError("'where' must be an object")
    try:
        return validate_filter_where(dict(raw))
    except ValueError as exc:
        raise LocatorError(str(exc)) from exc


def _optional_positive_int(raw: Any, field: str) -> int | None:
    if raw is None:
        return None
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise LocatorError(f"{field} must be an integer") from exc
    if value < 1:
        raise LocatorError(f"{field} must be >= 1 or omitted")
    return value
