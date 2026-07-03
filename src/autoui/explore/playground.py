"""
ExplorerSession — оркестратор playground для Jupyter.

Императивный обход pywinauto + проверка Locator через PywinautoDriver.
"""

from __future__ import annotations

from typing import Any

from autoui.drivers.pywinauto_driver import (
    PywinautoApp,
    PywinautoDriver,
    PywinautoElement,
    PywinautoWindow,
)
from autoui.drivers.pywinauto_tree import PywinautoElementTree
from autoui.explore.highlight import HighlightManager
from autoui.explore.pywinauto_helpers import (
    find_desktop_windows,
    path_from_root,
)
from autoui.locators.locator import Locator
from autoui.locators.trace import LocatorTrace


class ExplorerSession:
    """Сессия исследования одного целевого окна."""

    def __init__(
        self,
        window_title: str = "Notepad++",
        *,
        verbose_locators: bool = True,
    ) -> None:
        self.window_title = window_title
        self._verbose_locators = verbose_locators
        self._last_trace: LocatorTrace | None = None
        self._driver = PywinautoDriver(
            verbose_locators=verbose_locators,
            locator_trace_hook=self._on_trace,
        )
        self._tree = PywinautoElementTree()
        self._highlighter = HighlightManager()
        self._window_control: Any | None = None
        self._py_window: PywinautoWindow | None = None

    def _on_trace(self, trace: LocatorTrace) -> None:
        self._last_trace = trace
        if self._verbose_locators:
            print(trace.format_diagnostic())

    @staticmethod
    def find_desktop_windows(target_window_title: str) -> list[Any]:
        return find_desktop_windows(target_window_title)

    def connect(self, index: int = 0) -> Any:
        """
        Подключиться к окну по подстроке заголовка.

        Возвращает pywinauto control корня окна.
        """
        windows = find_desktop_windows(self.window_title)
        if not windows:
            raise RuntimeError(f"No desktop window matching '{self.window_title}'")
        if index >= len(windows):
            raise IndexError(
                f"Window index {index} out of range ({len(windows)} matches for '{self.window_title}')"
            )
        control = windows[index]
        handle = control.handle
        from pywinauto.application import Application

        app = Application(backend="uia").connect(handle=handle)
        py_app = PywinautoApp(native_id=handle, app=app)
        py_win = PywinautoWindow(native_handle=handle, window=control)
        self._driver.set_primary(py_app, py_win)
        self._window_control = control
        self._py_window = py_win
        return control

    @property
    def window(self) -> Any:
        if self._window_control is None:
            raise RuntimeError("Call connect() first")
        return self._window_control

    @property
    def driver(self) -> PywinautoDriver:
        return self._driver

    @property
    def last_trace(self) -> LocatorTrace | None:
        return self._last_trace

    def children(self, node: Any | None = None) -> list[Any]:
        root = node if node is not None else self.window
        return list(root.children())

    def descendants(self, node: Any | None = None, **filters: Any) -> list[Any]:
        root = node if node is not None else self.window
        if filters:
            return list(root.descendants(**filters))
        return list(root.descendants())

    def list_indexed(self, controls: list[Any]) -> None:
        """Печать [i] control_type | name | automation_id для подбора индекса."""
        for i, ctrl in enumerate(controls):
            props = self._tree.properties(ctrl)
            name = props.name or ""
            auto_id = props.automation_id or ""
            ct = props.control_type or ""
            print(f"[{i}] {ct} | {name!r} | auto_id={auto_id!r}")

    def describe(self, control: Any) -> None:
        """Свойства элемента и путь от корня."""
        props = self._tree.properties(control)
        print(props)
        print(path_from_root(control))

    def highlight(
        self,
        control: Any,
        *,
        colour: str | int = "green",
        thickness: int = 4,
    ) -> None:
        self._highlighter.highlight(control, colour=colour, thickness=thickness)

    def clear_highlight(self) -> None:
        self._highlighter.clear()

    def try_locator(
        self,
        locator: Locator,
        *,
        highlight: bool = True,
    ) -> PywinautoElement | None:
        """
        resolve через драйвер; при успехе — подсветка control.

        При not-found печатает trace (если verbose_locators).
        """
        self._last_trace = None
        element = self._driver.resolve(locator, self._py_window)
        if element is None:
            return None
        if highlight:
            self.highlight(element.control)
        return element
