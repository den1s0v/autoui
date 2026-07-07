"""Unit tests for locator_codegen."""

from __future__ import annotations

from autoui.explore.inspector.hierarchy_navigator import PathSegment
from autoui.explore.inspector.locator_codegen import (
    codegen_from_navigator,
    locator_from_control_segments,
    locator_to_python,
    parse_locator_python,
)
from autoui.locators import ChildOp, FindDescendantsOp, Locator, TakeOp


class _Ctrl:
    pass


def _seg(index: int, label: str) -> PathSegment:
    return PathSegment(control=_Ctrl(), child_index=index, label=label, kind="control")


def test_locator_from_control_segments() -> None:
    loc = locator_from_control_segments([_seg(1, "a"), _seg(2, "b")])
    assert loc.ops == (ChildOp(1), ChildOp(2))


def test_locator_to_python_round_trip() -> None:
    source = codegen_from_navigator(
        [_seg(1, "Pane | P2"), _seg(2, "Button | OK")],
        PathSegment(control=_Ctrl(), child_index=0, label="Notepad++", kind="window"),
    )
    parsed = parse_locator_python(source)
    assert parsed.ops == (ChildOp(1), ChildOp(2))


def test_parse_custom_locator_with_find() -> None:
    text = """
from autoui.locators import Locator, FindDescendantsOp, TakeOp
Locator([
    FindDescendantsOp(where={"name": "OK"}),
    TakeOp(0),
])
"""
    loc = parse_locator_python(text)
    assert len(loc.ops) == 2
    assert isinstance(loc.ops[0], FindDescendantsOp)
    assert isinstance(loc.ops[1], TakeOp)


def test_codegen_without_window() -> None:
    text = codegen_from_navigator([], None)
    assert "Select a window" in text
