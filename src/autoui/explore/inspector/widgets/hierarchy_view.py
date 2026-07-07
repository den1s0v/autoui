"""
HierarchyView — двухуровневый список PATH + CHILDREN с клавиатурной навигацией.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QKeyEvent
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from autoui.explore.inspector.hierarchy_navigator import (
    FocusZone,
    HierarchyNavigator,
    NavKey,
    ViewRow,
)

_ITEM_DATA = Qt.ItemDataRole.UserRole
_COMMITTED_BG = QColor(180, 210, 255)
_FOCUS_BG = QColor(200, 230, 200)


class HierarchyView(QWidget):
    """Левая панель: PATH и CHILDREN в одном QListWidget."""

    path_changed = Signal()
    highlight_requested = Signal()

    def __init__(self, navigator: HierarchyNavigator, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._nav = navigator
        self._list = QListWidget(self)
        self._list.setAlternatingRowColors(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._list)
        self._list.itemActivated.connect(self._on_item_activated)
        self._list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.setFocusProxy(self._list)

    def navigator(self) -> HierarchyNavigator:
        return self._nav

    def refresh(self) -> None:
        self._list.clear()
        for row in self._nav.build_view_rows():
            item = QListWidgetItem(row.label)
            item.setData(_ITEM_DATA, row)
            if row.is_committed:
                item.setBackground(_COMMITTED_BG)
            elif row.has_focus:
                item.setBackground(_FOCUS_BG)
            self._list.addItem(item)
        self._sync_list_focus()
        self.path_changed.emit()

    def _sync_list_focus(self) -> None:
        rows = self._nav.build_view_rows()
        focus_idx = next((i for i, r in enumerate(rows) if r.has_focus), -1)
        if focus_idx >= 0:
            self._list.setCurrentRow(focus_idx)

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
            self.refresh()
            event.accept()
            return
        if event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Return):
            self.highlight_requested.emit()
            event.accept()
            return
        super().keyPressEvent(event)

    def _on_item_activated(self, item: QListWidgetItem) -> None:
        row: ViewRow | None = item.data(_ITEM_DATA)
        if row is None:
            return
        if row.zone == "path":
            self._nav.focus_zone = FocusZone.PATH
            self._nav.focus_path_row = row.path_row
        else:
            self._nav.focus_zone = FocusZone.CHILDREN
            self._nav.focus_child_index = row.child_index or 0
        self.refresh()
        self.highlight_requested.emit()

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        row: ViewRow | None = item.data(_ITEM_DATA)
        if row is not None:
            if row.zone == "path":
                self._nav.focus_zone = FocusZone.PATH
                self._nav.focus_path_row = row.path_row
            else:
                self._nav.focus_zone = FocusZone.CHILDREN
                self._nav.focus_child_index = row.child_index or 0
            self.refresh()
        self.highlight_requested.emit()
