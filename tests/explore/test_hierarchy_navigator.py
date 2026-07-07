"""Unit tests for HierarchyNavigator keyboard logic."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from autoui.explore.inspector.hierarchy_navigator import (
    FocusZone,
    HierarchyNavigator,
    NavKey,
    PathSegment,
)


@dataclass
class MockControl:
    name: str
    children_list: list[MockControl] = field(default_factory=list)
    handle: int = 0

    def __post_init__(self) -> None:
        if self.handle == 0:
            self.handle = id(self)

    def children(self) -> list[MockControl]:
        return self.children_list

    def windows(self) -> list[MockControl]:
        return self.children_list

    def window_text(self) -> str:
        return self.name

    def class_name(self) -> str:
        return "Mock"


def _seg(control: MockControl, index: int, *, window: bool = False) -> PathSegment:
    kind = "window" if window else "control"
    return PathSegment(
        control=control,
        child_index=index,
        label=control.name,
        kind=kind,
    )


def _tree() -> tuple[MockControl, MockControl, MockControl, MockControl]:
    """Desktop → W0(W1, W2) where W1 has Btn."""
    btn = MockControl("Btn211")
    p21 = MockControl("P21", [btn])
    p22 = MockControl("P22")
    p2 = MockControl("P2", [p21, p22])
    p1 = MockControl("P1")
    desktop = MockControl("Desktop", [p1, p2])
    return desktop, p1, p2, btn


def _nav_with_loader(desktop: MockControl) -> HierarchyNavigator:
    nav = HierarchyNavigator(desktop=desktop)

    def loader(parent: Any) -> list[Any]:
        if parent is desktop:
            return parent.windows()
        return parent.children()

    nav._children_loader = loader
    return nav


def test_right_on_path_expands_children() -> None:
    desktop, p1, p2, _ = _tree()
    nav = _nav_with_loader(desktop)
    nav.handle_key(NavKey.RIGHT)
    assert nav.children_expanded
    assert nav.focus_zone == FocusZone.CHILDREN
    assert len(nav.children) == 2
    assert nav.children[0].control is p1


def test_right_on_child_commits_and_focuses_new_path_row() -> None:
    desktop, p1, p2, _ = _tree()
    nav = _nav_with_loader(desktop)
    nav.handle_key(NavKey.RIGHT)
    nav.focus_child_index = 1
    nav.handle_key(NavKey.RIGHT)
    assert len(nav.path) == 1
    assert nav.path[0].control is p2
    assert nav.focus_zone == FocusZone.PATH
    assert nav.focus_path_row == 1
    assert nav.children_expanded
    assert len(nav.children) == 2


def test_committed_child_highlight_index() -> None:
    desktop, _, p2, _ = _tree()
    nav = _nav_with_loader(desktop)
    p21 = p2.children_list[0]
    nav.path = [_seg(p2, 1, window=True), _seg(p21, 0)]
    nav.explore_path_row = 1
    nav.children_expanded = True
    nav.refresh_children()
    assert nav.committed_child_index() == 0


def test_truncate_path_on_reselect_sibling() -> None:
    desktop, p1, p2, _ = _tree()
    nav = _nav_with_loader(desktop)
    nav.path = [_seg(p2, 1, window=True), _seg(p2.children_list[0], 0)]
    nav.explore_path_row = 1
    nav.children_expanded = True
    nav.refresh_children()
    nav.focus_zone = FocusZone.CHILDREN
    nav.focus_child_index = 1
    nav.handle_key(NavKey.RIGHT)
    assert len(nav.path) == 2
    assert nav.path[1].control is p2.children_list[1]


def test_left_from_children_returns_to_path() -> None:
    desktop, _, _, _ = _tree()
    nav = _nav_with_loader(desktop)
    nav.handle_key(NavKey.RIGHT)
    nav.handle_key(NavKey.LEFT)
    assert nav.focus_zone == FocusZone.PATH


def test_down_from_path_enters_children() -> None:
    desktop, _, p2, _ = _tree()
    nav = _nav_with_loader(desktop)
    nav.path = [_seg(p2, 1, window=True)]
    nav.explore_path_row = 1
    nav.children_expanded = True
    nav.refresh_children()
    nav.focus_path_row = 1
    nav.handle_key(NavKey.DOWN)
    assert nav.focus_zone == FocusZone.CHILDREN
    assert nav.focus_child_index == 0
