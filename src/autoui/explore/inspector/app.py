"""
MainWindow Control Inspector — wiring ExplorerSession, навигация, подсветка.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from autoui.explore.highlight import HighlightManager
from autoui.explore.inspector.hierarchy_navigator import HierarchyNavigator
from autoui.explore.inspector.locator_codegen import codegen_from_navigator, parse_locator_python
from autoui.explore.inspector.widgets.hierarchy_view import HierarchyView
from autoui.explore.inspector.widgets.properties_panel import PropertiesPanel
from autoui.explore.inspector.widgets.selector_panel import SelectorMode, SelectorPanel
from autoui.explore.playground import ExplorerSession
from autoui.locators.errors import LocatorError


def _create_desktop() -> Any:
    from pywinauto import Desktop

    return Desktop(backend="uia")


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("autoUI Control Inspector")
        self.resize(1100, 700)

        desktop = _create_desktop()
        self._nav = HierarchyNavigator(desktop=desktop)
        self._nav._expand_children_at(0)

        self._session: ExplorerSession | None = None
        self._connected_window_id: int | None = None
        self._highlighter = HighlightManager()

        self._hierarchy = HierarchyView(self._nav)
        self._properties = PropertiesPanel()
        self._selector = SelectorPanel()

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.addWidget(self._properties, stretch=2)
        right_layout.addWidget(self._selector, stretch=1)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._hierarchy)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        self.setCentralWidget(splitter)

        toolbar = QToolBar("Main")
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self._on_refresh)
        toolbar.addAction(refresh_action)
        self.addToolBar(toolbar)

        self._status = QStatusBar()
        self.setStatusBar(self._status)

        self._hierarchy.path_changed.connect(self._on_path_changed)
        self._hierarchy.highlight_requested.connect(self._on_highlight)
        self._selector.test_requested.connect(self._on_test)
        self._selector.copy_requested.connect(self._on_copy)

        self._hierarchy.refresh()
        self._status.showMessage("Desktop — выберите окно (→ на дочернем элементе)")

    def _ensure_session_for_window(self) -> ExplorerSession | None:
        window_seg = self._nav.window_segment()
        if window_seg is None:
            return None
        control = window_seg.control
        handle = control.handle
        if self._session is not None and self._connected_window_id == handle:
            return self._session
        self._session = ExplorerSession(verbose_locators=False)
        try:
            self._session.connect_control(control)
        except Exception as exc:
            self._status.showMessage(f"Connect failed: {exc}")
            self._session = None
            self._connected_window_id = None
            return None
        self._connected_window_id = handle
        self._status.showMessage(f"Connected: {window_seg.label}")
        return self._session

    def _on_path_changed(self) -> None:
        self._ensure_session_for_window()
        control = self._nav.selected_control()
        self._properties.show_control(control)
        if self._selector.mode() == SelectorMode.GENERATED:
            text = codegen_from_navigator(
                self._nav.control_segments(),
                self._nav.window_segment(),
            )
            self._selector.set_generated_text(text)

    def _on_refresh(self) -> None:
        self.setCursor(Qt.CursorShape.WaitCursor)
        try:
            self._nav.refresh_children()
            self._hierarchy.refresh()
        finally:
            self.unsetCursor()

    def _on_highlight(self) -> None:
        control = self._nav.focused_control()
        if control is None:
            return
        session = self._ensure_session_for_window()
        if session is not None and self._nav.window_segment() is not None:
            session.highlight(control)
        else:
            self._highlighter.highlight(control)

    def _on_test(self) -> None:
        session = self._ensure_session_for_window()
        if session is None:
            QMessageBox.warning(
                self,
                "Test",
                "Сначала выберите окно в иерархии Desktop.",
            )
            return
        try:
            locator = parse_locator_python(self._selector.editor_text())
        except LocatorError as exc:
            QMessageBox.warning(self, "Test", str(exc))
            return
        element = session.try_locator(locator, highlight=True)
        if element is None:
            QMessageBox.warning(self, "Test", "Locator not found")
            self._status.showMessage("Test failed: not found")
            return
        self._status.showMessage("Test OK — element highlighted")

    def _on_copy(self) -> None:
        QApplication.clipboard().setText(self._selector.editor_text())
        self._status.showMessage("Copied to clipboard")


def run_inspector() -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
