"""
PywinautoDriver — реализация IDriver через UIA backend.

Обёртки PywinautoApp/Window/Element реализуют AppHandle, WindowHandle, UIElement.
Resolve через LocatorExecutor; not-found → None / False.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from autoui.core.exceptions import DriverError
from autoui.drivers.pywinauto_tree import PywinautoElementTree
from autoui.locators import Locator, LocatorExecutor, LocatorNotFoundError
from autoui.locators.trace import LocatorTrace
from autoui.uimap.map import UIMap

logger = logging.getLogger("autoui.locator")


@dataclass
class PywinautoApp:
    native_id: int
    app: Any

    @property
    def application(self) -> Any:
        return self.app


@dataclass
class PywinautoWindow:
    native_handle: int
    window: Any


@dataclass
class PywinautoElement:
    """UIElement — обёртка над pywinauto control."""

    control: Any

    def click(self, internally: bool = True) -> None:
        """Click on the element.

        Args:
            internally: If True, simulate click internally without moving the mouse (click).
            If False, click on the element using the mouse (click_input).
        """
        if internally:
            self.control.click()
        else:
            self.control.click_input()

    def set_text(self, text: str) -> None:
        self.control.set_edit_text(text)

    def get_text(self) -> str:
        return self.control.window_text()

    def get_value(self) -> str:
        try:
            return self.control.get_value()
        except Exception:
            return self.get_text()

    def is_enabled(self) -> bool:
        return self.control.is_enabled()


class PywinautoDriver:
    """
    UIA-драйвер. Требует pywinauto и pywin32.

    uimap передаётся при создании или берётся из ctx в actions.
  """

    def __init__(
        self,
        uimap: UIMap | None = None,
        *,
        locator_trace_hook: Callable[[LocatorTrace], None] | None = None,
        verbose_locators: bool = False,
    ) -> None:
        self._uimap = uimap
        self._primary_app: PywinautoApp | None = None
        self._primary_window: PywinautoWindow | None = None
        self._desktop: Any = None
        self._locator_trace_hook = locator_trace_hook
        self._verbose_locators = verbose_locators
        self._executor = LocatorExecutor()
        self._tree = PywinautoElementTree()

    def _get_desktop(self) -> Any:
        if self._desktop is None:
            from pywinauto import Desktop

            self._desktop = Desktop(backend="uia")
        return self._desktop

    def _resolve_target(
        self, target: str | Locator | PywinautoElement
    ) -> Locator | PywinautoElement:
        if isinstance(target, PywinautoElement):
            return target
        if isinstance(target, Locator):
            return target
        if self._uimap is None:
            raise DriverError("UIMap required to resolve string target")
        return self._uimap.resolve(target)

    def _window_spec(self, window: PywinautoWindow | None) -> Any:
        win = window or self._primary_window
        if win is None:
            raise DriverError("No window: call set_primary or pass window=")
        return win.window

    def _emit_trace(self, trace: LocatorTrace) -> None:
        if self._locator_trace_hook is not None:
            self._locator_trace_hook(trace)
        elif self._verbose_locators:
            logger.debug(trace.format_diagnostic())

    def _execute_locator(
        self,
        locator: Locator,
        window: PywinautoWindow | None,
    ) -> PywinautoElement | None:
        root = self._window_spec(window)
        try:
            result = self._executor.execute(self._tree, root, locator)
            if result.truncated_from is not None:
                logger.warning(
                    "Locator matched %d elements; using first only (add Take op to be explicit)",
                    result.truncated_from,
                )
            if self._verbose_locators:
                self._emit_trace(result.trace)
            return PywinautoElement(control=result.node)
        except LocatorNotFoundError as exc:
            self._emit_trace(exc.trace)
            return None

    def _require_element(
        self,
        target: str | Locator | PywinautoElement,
        window: PywinautoWindow | None,
    ) -> PywinautoElement:
        resolved = self._resolve_target(target)
        if isinstance(resolved, PywinautoElement):
            return resolved
        element = self._execute_locator(resolved, window)
        if element is None:
            raise DriverError(f"Element not found: {target!r}")
        return element

    def connect_running_app(self, selector: str | int) -> PywinautoApp:
        from pywinauto.application import Application

        try:
            if isinstance(selector, int):
                app = Application(backend="uia").connect(handle=selector)
                handle = selector
            else:
                desktop = self._get_desktop()
                target = None
                for w in desktop.windows():
                    if selector in (w.window_text() or ""):
                        target = w
                        break
                if target is None:
                    raise DriverError(f"No window matching '{selector}'")
                handle = target.handle
                app = Application(backend="uia").connect(handle=handle)
            return PywinautoApp(native_id=handle, app=app)
        except DriverError:
            raise
        except Exception as exc:
            raise DriverError(str(exc)) from exc

    def attach_window(
        self,
        app: PywinautoApp,
        *,
        title: str | None = None,
        handle: int | None = None,
    ) -> PywinautoWindow:
        try:
            if handle is not None:
                win = app.application.window(handle=handle)
            elif title:
                win = app.application.window(title_re=f".*{title}.*")
            else:
                win = app.application.top_window()
            return PywinautoWindow(native_handle=win.handle, window=win)
        except Exception as exc:
            raise DriverError(str(exc)) from exc

    def set_primary(
        self,
        app: PywinautoApp | None = None,
        window: PywinautoWindow | None = None,
    ) -> None:
        if app is not None:
            self._primary_app = app
        if window is not None:
            self._primary_window = window

    def resolve(
        self,
        target: str | Locator | PywinautoElement,
        window: PywinautoWindow | None = None,
    ) -> PywinautoElement | None:
        resolved = self._resolve_target(target)
        if isinstance(resolved, PywinautoElement):
            return resolved
        return self._execute_locator(resolved, window)

    def click(
        self,
        target: str | Locator | PywinautoElement,
        window: PywinautoWindow | None = None,
    ) -> None:
        self._require_element(target, window).click()

    def set_text(
        self,
        target: str | Locator | PywinautoElement,
        text: str,
        window: PywinautoWindow | None = None,
    ) -> None:
        self._require_element(target, window).set_text(text)

    def get_text(
        self,
        target: str | Locator | PywinautoElement,
        window: PywinautoWindow | None = None,
    ) -> str:
        return self._require_element(target, window).get_text()

    def get_value(
        self,
        target: str | Locator | PywinautoElement,
        window: PywinautoWindow | None = None,
    ) -> str:
        return self._require_element(target, window).get_value()

    def check_checkbox(
        self,
        target: str | Locator | PywinautoElement,
        checked: bool,
        window: PywinautoWindow | None = None,
    ) -> None:
        el = self._require_element(target, window)
        current = el.get_value()
        is_on = current in ("1", "True", "true", "Checked")
        if is_on != checked:
            el.click()

    def exists(
        self,
        target: str | Locator | PywinautoElement,
        window: PywinautoWindow | None = None,
    ) -> bool:
        try:
            resolved = self._resolve_target(target)
            if isinstance(resolved, PywinautoElement):
                return resolved.control.exists()
            return self._execute_locator(resolved, window) is not None
        except DriverError:
            return False

    def is_enabled(
        self,
        target: str | Locator | PywinautoElement,
        window: PywinautoWindow | None = None,
    ) -> bool:
        element = self.resolve(target, window)
        if element is None:
            return False
        return element.is_enabled()

    def activate_window(self, window: PywinautoWindow | None = None) -> None:
        self._window_spec(window).set_focus()

    def press_hotkey(self, *keys: str) -> None:
        from pywinauto.keyboard import send_keys

        combo = "".join(f"{{{k}}}" for k in keys)
        send_keys(combo)

    def wait(self, timeout: float) -> None:
        import time

        time.sleep(timeout)

    def window_exists(self, title_substring: str, app: PywinautoApp | None = None) -> bool:
        try:
            desktop = self._get_desktop()
            return any(title_substring in (w.window_text() or "") for w in desktop.windows())
        except Exception:
            return False

    def get_foreground_window(self) -> PywinautoWindow | None:
        try:
            import win32gui

            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                from pywinauto.application import Application

                app = Application(backend="uia").connect(handle=hwnd)
                win = app.window(handle=hwnd)
                return PywinautoWindow(native_handle=hwnd, window=win)
        except Exception:
            pass
        return None

    def set_foreground(self, window: PywinautoWindow) -> None:
        try:
            import win32con
            import win32gui

            hwnd = window.native_handle
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
        except Exception as exc:
            raise DriverError(str(exc)) from exc

    def bind_uimap(self, uimap: UIMap) -> None:
        self._uimap = uimap
