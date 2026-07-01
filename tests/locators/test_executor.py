"""Unit tests for LocatorExecutor."""

from __future__ import annotations

import pytest

from autoui.locators import (
    ChildOp,
    FilterOp,
    FindDescendantsOp,
    Locator,
    LocatorExecutor,
    LocatorNotFoundError,
    TakeOp,
)
from tests.locators.conftest import MockElementTree, build_sample_tree

@pytest.fixture
def tree() -> MockElementTree:
    return MockElementTree()


@pytest.fixture
def root():
    return build_sample_tree()


def test_path_child_navigation(tree: MockElementTree, root) -> None:
    # root → pane[1] → custom → button[0] (Экспорт)
    locator = Locator([ChildOp(1), ChildOp(0), ChildOp(0)])
    result = LocatorExecutor().execute(tree, root, locator)
    props = tree.properties(result.node)
    assert props.name == "Экспорт"
    assert len(result.trace.steps) == 3
    assert result.trace.failed_step_index is None


def test_find_descendants_filter_take(tree: MockElementTree, root) -> None:
    locator = Locator(
        [
            FindDescendantsOp(where={"control_type": "Button"}),
            FilterOp(where={"name": "Экспорт"}),
            TakeOp(0),
        ]
    )
    result = LocatorExecutor().execute(tree, root, locator)
    assert tree.properties(result.node).name == "Экспорт"


def test_shorthand_find(tree: MockElementTree, root) -> None:
    locator = Locator.find(automation_id="btnOk")
    result = LocatorExecutor().execute(tree, root, locator)
    assert tree.properties(result.node).name == "OK"


def test_filter_empty_raises_with_trace(tree: MockElementTree, root) -> None:
    locator = Locator(
        [
            FindDescendantsOp(where={"control_type": "Button"}),
            FilterOp(where={"name": "Несуществует"}),
            TakeOp(0),
        ]
    )
    with pytest.raises(LocatorNotFoundError) as exc_info:
        LocatorExecutor().execute(tree, root, locator)
    exc = exc_info.value
    assert exc.trace.failed_step_index == 1
    assert exc.trace.failure_reason == "empty_set"
    diag = exc.trace.format_diagnostic()
    assert "FAILED" in diag
    assert "in=3" in diag or "in=2" in diag


def test_take_index_out_of_range(tree: MockElementTree, root) -> None:
    locator = Locator(
        [
            FindDescendantsOp(where={"control_type": "Button", "name": "Экспорт"}),
            TakeOp(1),
        ]
    )
    with pytest.raises(LocatorNotFoundError) as exc_info:
        LocatorExecutor().execute(tree, root, locator)
    assert exc_info.value.trace.failure_reason == "take_index_out_of_range"


def test_child_out_of_range(tree: MockElementTree, root) -> None:
    locator = Locator([ChildOp(99)])
    with pytest.raises(LocatorNotFoundError) as exc_info:
        LocatorExecutor().execute(tree, root, locator)
    assert exc_info.value.trace.failed_step_index == 0
    assert exc_info.value.trace.failure_reason == "empty_set"


def test_format_diagnostic_success(tree: MockElementTree, root) -> None:
    locator = Locator.find(name="OK")
    result = LocatorExecutor().execute(tree, root, locator)
    diag = result.trace.format_diagnostic()
    assert "success" in diag
    assert "find_descendants" in diag
