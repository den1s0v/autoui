"""
HierarchyNavigator — state machine навигации Desktop → окно → контролы.

Без Qt; покрывается unit-тестами. См. README — Control Inspector.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Literal

from autoui.explore.inspector.control_label import (
    DESKTOP_LABEL,
    format_control_label,
    format_window_label,
)
from autoui.drivers.pywinauto_tree import PywinautoElementTree

SegmentKind = Literal["window", "control"]


class FocusZone(Enum):
    PATH = auto()
    CHILDREN = auto()


class NavKey(Enum):
    LEFT = auto()
    RIGHT = auto()
    UP = auto()
    DOWN = auto()


@dataclass(frozen=True)
class PathSegment:
    control: Any
    child_index: int
    label: str
    kind: SegmentKind


@dataclass
class ViewRow:
    """Строка для отрисовки в HierarchyView."""

    zone: Literal["path", "child"]
    label: str
    path_row: int
    child_index: int | None = None
    is_committed: bool = False
    has_focus: bool = False


@dataclass
class HierarchyNavigator:
    """
    Навигация по иерархии pywinauto от Desktop.

    path_row: 0 = Desktop; k>=1 → path[k-1].
    explore_row: какой сегмент PATH раскрывает children (-1 логически = row 0).
    """

    desktop: Any
    path: list[PathSegment] = field(default_factory=list)
    focus_zone: FocusZone = FocusZone.PATH
    focus_path_row: int = 0
    focus_child_index: int = 0
    explore_path_row: int = 0
    children_expanded: bool = False
    children: list[PathSegment] = field(default_factory=list)
    _tree: PywinautoElementTree = field(default_factory=PywinautoElementTree)
    _children_loader: Callable[[Any], list[Any]] | None = None

    def path_row_count(self) -> int:
        return 1 + len(self.path)

    def explore_row(self) -> int:
        """PATH row, чьи дети показаны в CHILDREN."""
        if self.children_expanded:
            return self.explore_path_row
        return max(0, self.path_row_count() - 1)

    def _parent_control_for_row(self, path_row: int) -> Any:
        if path_row <= 0:
            return self.desktop
        return self.path[path_row - 1].control

    def _is_desktop_row(self, path_row: int) -> bool:
        return path_row <= 0

    def _load_children_raw(self, parent: Any, *, from_desktop: bool) -> list[Any]:
        if self._children_loader is not None:
            return self._children_loader(parent)
        if from_desktop:
            return list(parent.windows())
        return list(parent.children())

    def _make_segment(self, control: Any, index: int, *, from_desktop: bool) -> PathSegment:
        if from_desktop:
            return PathSegment(
                control=control,
                child_index=index,
                label=format_window_label(control),
                kind="window",
            )
        return PathSegment(
            control=control,
            child_index=index,
            label=format_control_label(control),
            kind="control",
        )

    def refresh_children(self) -> None:
        """Перечитать children активного explore-сегмента."""
        row = self.explore_row()
        from_desktop = self._is_desktop_row(row)
        parent = self._parent_control_for_row(row)
        raw = self._load_children_raw(parent, from_desktop=from_desktop)
        self.children = [
            self._make_segment(ctrl, i, from_desktop=from_desktop)
            for i, ctrl in enumerate(raw)
        ]

    def _expand_children_at(self, path_row: int) -> None:
        self.explore_path_row = path_row
        self.children_expanded = True
        self.refresh_children()
        self.focus_zone = FocusZone.CHILDREN
        self.focus_child_index = 0 if self.children else 0

    def _collapse_children(self) -> None:
        self.children_expanded = False
        self.children = []

    def committed_child_index(self) -> int | None:
        """
        Индекс ребёнка в children, являющегося следующим сегментом path.

        Для explore_path_row=k committed = path[k].child_index, если сегмент есть.
        """
        if not self.children_expanded:
            return None
        row = self.explore_row()
        if row >= len(self.path):
            return None
        return self.path[row].child_index

    def focused_control(self) -> Any | None:
        """Control под фокусом клавиатуры; Desktop → None."""
        if self.focus_zone == FocusZone.PATH:
            if self.focus_path_row <= 0:
                return None
            return self.path[self.focus_path_row - 1].control
        if not self.children or self.focus_child_index >= len(self.children):
            return None
        return self.children[self.focus_child_index].control

    def selected_control(self) -> Any | None:
        """Последний зафиксированный узел path; пустой path → None (Desktop)."""
        if not self.path:
            return None
        return self.path[-1].control

    def window_segment(self) -> PathSegment | None:
        for seg in self.path:
            if seg.kind == "window":
                return seg
        return None

    def control_segments(self) -> list[PathSegment]:
        """Сегменты path после окна — для codegen Locator."""
        found_window = False
        result: list[PathSegment] = []
        for seg in self.path:
            if seg.kind == "window":
                found_window = True
                continue
            if found_window:
                result.append(seg)
        return result

    def handle_key(self, key: NavKey) -> None:
        if key == NavKey.RIGHT:
            self._on_right()
        elif key == NavKey.LEFT:
            self._on_left()
        elif key == NavKey.UP:
            self._on_up()
        elif key == NavKey.DOWN:
            self._on_down()

    def _on_right(self) -> None:
        if self.focus_zone == FocusZone.PATH:
            self._expand_children_at(self.focus_path_row)
            return

        if not self.children:
            return
        child = self.children[self.focus_child_index]
        explore = self.explore_row()
        self.path = self.path[:explore]
        self.path.append(child)
        new_row = len(self.path)
        self.focus_zone = FocusZone.PATH
        self.focus_path_row = new_row
        self.explore_path_row = new_row
        self.children_expanded = True
        self.refresh_children()

    def _on_left(self) -> None:
        if self.focus_zone == FocusZone.CHILDREN:
            self.focus_zone = FocusZone.PATH
            self.focus_path_row = self.explore_row()
            return
        if self.children_expanded and self.explore_row() == self.focus_path_row:
            self._collapse_children()

    def _on_up(self) -> None:
        if self.focus_zone == FocusZone.PATH:
            if self.focus_path_row > 0:
                self.focus_path_row -= 1
            return
        if self.focus_child_index > 0:
            self.focus_child_index -= 1
            return
        self.focus_zone = FocusZone.PATH
        self.focus_path_row = self.explore_row()

    def _on_down(self) -> None:
        if self.focus_zone == FocusZone.PATH:
            if self.focus_path_row < self.path_row_count() - 1:
                self.focus_path_row += 1
            elif self.children_expanded and self.children:
                self.focus_zone = FocusZone.CHILDREN
                self.focus_child_index = 0
            return
        if self.focus_child_index < len(self.children) - 1:
            self.focus_child_index += 1
            return
        self.focus_zone = FocusZone.PATH
        if self.focus_path_row < self.path_row_count() - 1:
            self.focus_path_row += 1

    def build_view_rows(self) -> list[ViewRow]:
        """Плоский список строк PATH + CHILDREN для виджета."""
        rows: list[ViewRow] = []
        committed = self.committed_child_index()
        explore = self.explore_row()

        rows.append(
            ViewRow(
                zone="path",
                label=DESKTOP_LABEL,
                path_row=0,
                has_focus=(
                    self.focus_zone == FocusZone.PATH and self.focus_path_row == 0
                ),
            )
        )

        if self.children_expanded and explore == 0:
            for seg in self.children:
                rows.append(
                    ViewRow(
                        zone="child",
                        label=f"> {seg.label}",
                        path_row=0,
                        child_index=seg.child_index,
                        is_committed=committed == seg.child_index,
                        has_focus=(
                            self.focus_zone == FocusZone.CHILDREN
                            and self.focus_child_index == seg.child_index
                        ),
                    )
                )

        for i, seg in enumerate(self.path):
            path_row = i + 1
            rows.append(
                ViewRow(
                    zone="path",
                    label=seg.label,
                    path_row=path_row,
                    has_focus=(
                        self.focus_zone == FocusZone.PATH
                        and self.focus_path_row == path_row
                    ),
                )
            )
            if self.children_expanded and explore == path_row:
                for child in self.children:
                    rows.append(
                        ViewRow(
                            zone="child",
                            label=f"> {child.label}",
                            path_row=path_row,
                            child_index=child.child_index,
                            is_committed=committed == child.child_index,
                            has_focus=(
                                self.focus_zone == FocusZone.CHILDREN
                                and self.focus_child_index == child.child_index
                            ),
                        )
                    )
        return rows

    def set_path_from_segments(self, segments: list[PathSegment], *, explore_row: int | None = None) -> None:
        """Синхронизация path извне (codegen / будущий Test-rebuild)."""
        self.path = list(segments)
        self.focus_zone = FocusZone.PATH
        self.focus_path_row = len(self.path)
        row = explore_row if explore_row is not None else len(self.path)
        self.explore_path_row = row
        self.children_expanded = True
        self.refresh_children()
        if self.children:
            committed = self.committed_child_index()
            if committed is not None and committed < len(self.children):
                self.focus_zone = FocusZone.CHILDREN
                self.focus_child_index = committed
