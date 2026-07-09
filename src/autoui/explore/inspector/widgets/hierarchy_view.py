"""
HierarchyView — PATH + вложенные CHILDREN на QTreeWidget.

Дети отображаются как раскрывающиеся подпункты (disclosure triangle), без префикса «>».
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QKeyEvent, QMouseEvent
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

from autoui.explore.inspector.control_label import DESKTOP_LABEL
from autoui.explore.inspector.hierarchy_navigator import (
    FocusZone,
    HierarchyNavigator,
    NavKey,
)

_ITEM_DATA = Qt.ItemDataRole.UserRole
_COMMITTED_BG = QColor(180, 210, 255)
_FOCUS_BG = QColor(200, 230, 200)
_CLICK_DELAY_MS = 220


class _HierarchyTree(QTreeWidget):
    """Дерево с клавиатурной навигацией через HierarchyNavigator."""

    def __init__(
        self,
        navigator: HierarchyNavigator,
        view: HierarchyView,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._nav = navigator
        self._view = view
        self.setHeaderHidden(True)
        self.setRootIsDecorated(True)
        self.setAlternatingRowColors(True)
        self.setUniformRowHeights(True)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key_map = {
            Qt.Key.Key_Left: NavKey.LEFT,
            Qt.Key.Key_Right: NavKey.RIGHT,
            Qt.Key.Key_Up: NavKey.UP,
            Qt.Key.Key_Down: NavKey.DOWN,
        }
        nav_key = key_map.get(event.key())
        if nav_key is not None:
            self._nav.handle_key(nav_key)
            self._view.refresh()
            event.accept()
            return
        if event.key() == Qt.Key.Key_Space:
            self._view.highlight_requested.emit()
            event.accept()
            return
        super().keyPressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        item = self.itemAt(event.pos())
        if item is not None and event.button() == Qt.MouseButton.LeftButton:
            self._view.handle_double_click(item)
            event.accept()
            return
        super().mouseDoubleClickEvent(event)


class HierarchyView(QWidget):
    """Левая панель: Desktop → path-сегменты; дети — вложенные узлы."""

    path_changed = Signal()
    highlight_requested = Signal()

    def __init__(self, navigator: HierarchyNavigator, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._nav = navigator
        self._tree = _HierarchyTree(navigator, self, self)
        self._pending_click_item: QTreeWidgetItem | None = None
        self._click_timer = QTimer(self)
        self._click_timer.setSingleShot(True)
        self._click_timer.setInterval(_CLICK_DELAY_MS)
        self._click_timer.timeout.connect(self._on_single_click_timeout)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._tree)
        self._tree.itemClicked.connect(self._on_item_clicked)
        self.setFocusProxy(self._tree)

    def navigator(self) -> HierarchyNavigator:
        return self._nav

    def handle_double_click(self, item: QTreeWidgetItem) -> None:
        self._click_timer.stop()
        self._pending_click_item = None
        self._apply_item_focus(item)
        self.refresh()
        self.highlight_requested.emit()

    def refresh(self) -> None:
        self._tree.blockSignals(True)
        self._tree.clear()
        committed = self._nav.committed_child_index()
        explore = self._nav.explore_row() if self._nav.children_expanded else -1

        desktop_item = self._make_path_item(DESKTOP_LABEL, path_row=0)
        self._tree.addTopLevelItem(desktop_item)
        if self._nav.children_expanded and explore == 0:
            self._add_child_items(desktop_item, committed)
            desktop_item.setExpanded(True)

        for i, seg in enumerate(self._nav.path):
            path_row = i + 1
            item = self._make_path_item(seg.label, path_row=path_row)
            self._tree.addTopLevelItem(item)
            if self._nav.children_expanded and explore == path_row:
                self._add_child_items(item, committed)
                item.setExpanded(True)

        self._sync_tree_focus()
        self._tree.blockSignals(False)
        self.path_changed.emit()

    def _make_path_item(self, label: str, *, path_row: int) -> QTreeWidgetItem:
        item = QTreeWidgetItem([label])
        item.setData(0, _ITEM_DATA, ("path", path_row, None))
        if self._nav.focus_zone == FocusZone.PATH and self._nav.focus_path_row == path_row:
            item.setBackground(0, _FOCUS_BG)
        return item

    def _add_child_items(self, parent: QTreeWidgetItem, committed: int | None) -> None:
        explore = self._nav.explore_row()
        for seg in self._nav.children:
            child = QTreeWidgetItem([seg.label])
            child.setData(0, _ITEM_DATA, ("child", explore, seg.child_index))
            if committed is not None and seg.child_index == committed:
                child.setBackground(0, _COMMITTED_BG)
            elif (
                self._nav.focus_zone == FocusZone.CHILDREN
                and self._nav.focus_child_index == seg.child_index
            ):
                child.setBackground(0, _FOCUS_BG)
            parent.addChild(child)

    def _sync_tree_focus(self) -> None:
        target = self._find_focus_item()
        if target is not None:
            self._tree.setCurrentItem(target)
            self._tree.scrollToItem(target)

    def _find_focus_item(self) -> QTreeWidgetItem | None:
        zone_want = "path" if self._nav.focus_zone == FocusZone.PATH else "child"
        path_row = (
            self._nav.focus_path_row
            if zone_want == "path"
            else self._nav.explore_path_row
        )
        child_index = self._nav.focus_child_index if zone_want == "child" else None

        for i in range(self._tree.topLevelItemCount()):
            top = self._tree.topLevelItem(i)
            if top is None:
                continue
            found = self._match_item(top, zone_want, path_row, child_index)
            if found is not None:
                return found
            for j in range(top.childCount()):
                child = top.child(j)
                if child is not None:
                    found = self._match_item(child, zone_want, path_row, child_index)
                    if found is not None:
                        return found
        return None

    @staticmethod
    def _match_item(
        item: QTreeWidgetItem,
        zone_want: str,
        path_row: int,
        child_index: int | None,
    ) -> QTreeWidgetItem | None:
        data = item.data(0, _ITEM_DATA)
        if not data:
            return None
        zone, row, cidx = data
        if zone == zone_want and row == path_row and cidx == child_index:
            return item
        return None

    def _apply_item_focus(self, item: QTreeWidgetItem | None) -> None:
        if item is None:
            return
        data = item.data(0, _ITEM_DATA)
        if not data:
            return
        zone, path_row, child_index = data
        if zone == "path":
            self._nav.focus_zone = FocusZone.PATH
            self._nav.focus_path_row = path_row
        else:
            self._nav.focus_zone = FocusZone.CHILDREN
            self._nav.explore_path_row = path_row
            self._nav.children_expanded = True
            self._nav.refresh_children()
            self._nav.focus_child_index = child_index if child_index is not None else 0

    def _on_item_clicked(self, item: QTreeWidgetItem, _column: int) -> None:
        if item is None:
            return
        self._pending_click_item = item
        self._click_timer.start()

    def _on_single_click_timeout(self) -> None:
        if self._pending_click_item is None:
            return
        self._apply_item_focus(self._pending_click_item)
        self._pending_click_item = None
        self.refresh()
