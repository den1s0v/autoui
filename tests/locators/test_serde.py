"""Unit tests for locator JSON serde."""

from __future__ import annotations

import pytest

from autoui.locators import (
    ChildOp,
    FilterOp,
    FindDescendantsOp,
    Locator,
    LocatorError,
    TakeOp,
    locator_from_dict,
    locator_from_json,
    locator_to_dict,
    locator_to_json,
)


def test_round_trip_full_pipeline() -> None:
    original = Locator(
        [
            ChildOp(2),
            ChildOp(0),
            FindDescendantsOp(where={"control_type": "Button", "name": "Экспорт"}),
            TakeOp(0),
        ]
    )
    data = locator_to_dict(original)
    restored = locator_from_dict(data)
    assert restored.ops == original.ops


def test_round_trip_json() -> None:
    original = Locator.find(class_name="ToolbarWindow32")
    text = locator_to_json(original)
    restored = locator_from_json(text)
    assert len(restored.ops) == 2


def test_shorthand_find_dict() -> None:
    locator = locator_from_dict({"find": {"name": "OK"}})
    assert len(locator.ops) == 2
    assert isinstance(locator.ops[0], FindDescendantsOp)
    assert isinstance(locator.ops[1], TakeOp)


def test_unknown_op_raises() -> None:
    with pytest.raises(LocatorError, match="Unknown op"):
        locator_from_dict({"ops": [{"op": "unknown"}]})


def test_unknown_filter_key_raises() -> None:
    with pytest.raises(LocatorError, match="Unknown filter"):
        locator_from_dict({"ops": [{"op": "filter", "where": {"bad_key": 1}}]})
