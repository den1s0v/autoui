"""PropertiesPanel — свойства выделенного control."""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from autoui.drivers.pywinauto_tree import PywinautoElementTree


class PropertiesPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._tree = PywinautoElementTree()
        self._table = QTableWidget(0, 2, self)
        self._table.setHorizontalHeaderLabels(["key", "value"])
        self._table.horizontalHeader().setStretchLastSection(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._table)

    def show_control(self, control: Any | None) -> None:
        self._table.setRowCount(0)
        if control is None:
            return
        props = self._tree.properties(control)
        for key in sorted(props):
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setItem(row, 0, QTableWidgetItem(str(key)))
            self._table.setItem(row, 1, QTableWidgetItem(repr(props[key])))
