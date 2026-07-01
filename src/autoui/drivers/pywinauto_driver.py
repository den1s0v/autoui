"""
PywinautoDriver — реализация IDriver через UIA backend.

Обёртки PywinautoApp/Window/Element реализуют AppHandle, WindowHandle, UIElement.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from autoui.core.exceptions import DriverError
from autoui.uimap.element_ref import ElementRef
from autoui.uimap.map import UIMap


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

    def click(self) -> None:
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

    def __init__(self, uimap: UIMap | None = None) -> None:
        self._uimap = uimap
        self._primary_app: PywinautoApp | None = None
        self._primary_window: PywinautoWindow | None = None
        self._desktop: Any = None

    def _get_desktop(self) -> Any:
        if self._desktop is None:
            from pywinauto import Desktop

            self._desktop = Desktop(backend="uia")
        return self._desktop

    def _resolve_target(self, target: str | ElementRef | PywinautoElement) -> ElementRef | PywinautoElement:
        if isinstance(target, PywinautoElement):
            return target
        if isinstance(target, ElementRef):
            return target
        if self._uimap is None:
            raise DriverError("UIMap required to resolve string target")
        return self._uimap.resolve(target)

    def _window_spec(self, window: PywinautoWindow | None) -> Any:
        win = window or self._primary_window
        if win is None:
            raise DriverError("No window: call set_primary or pass window=")
        return win.window

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
        target: str | ElementRef | PywinautoElement,
        window: PywinautoWindow | None = None,
    ) -> PywinautoElement:
        ref = self._resolve_target(target)
        if isinstance(ref, PywinautoElement):
            return ref
        spec = self._window_spec(window)
        kwargs: dict[str, Any] = {}
        if ref.automation_id:
            kwargs["auto_id"] = ref.automation_id
        if ref.title:
            kwargs["title"] = ref.title
        if ref.class_name:
            kwargs["class_name"] = ref.class_name
        if ref.control_type:
            kwargs["control_type"] = ref.control_type
        if ref.best_match:
            kwargs["best_match"] = ref.best_match
        try:
            ctrl = spec.child_window(**kwargs)
            ctrl.wait("exists", timeout=2)
            return PywinautoElement(control=ctrl)
        except Exception as exc:
            raise DriverError(f"resolve failed: {exc}") from exc

    def click(
        self,
        target: str | ElementRef | PywinautoElement,
        window: PywinautoWindow | None = None,
    ) -> None:
        self.resolve(target, window).click()

    def set_text(
        self,
        target: str | ElementRef | PywinautoElement,
        text: str,
        window: PywinautoWindow | None = None,
    ) -> None:
        self.resolve(target, window).set_text(text)

    def get_text(
        self,
        target: str | ElementRef | PywinautoElement,
        window: PywinautoWindow | None = None,
    ) -> str:
        return self.resolve(target, window).get_text()

    def get_value(
        self,
        target: str | ElementRef | PywinautoElement,
        window: PywinautoWindow | None = None,
    ) -> str:
        return self.resolve(target, window).get_value()

    def check_checkbox(
        self,
        target: str | ElementRef | PywinautoElement,
        checked: bool,
        window: PywinautoWindow | None = None,
    ) -> None:
        el = self.resolve(target, window)
        # UIA toggle pattern simplified
        current = el.get_value()
        is_on = current in ("1", "True", "true", "Checked")
        if is_on != checked:
            el.click()

    def exists(
        self,
        target: str | ElementRef | PywinautoElement,
        window: PywinautoWindow | None = None,
    ) -> bool:
        try:
            ref = self._resolve_target(target)
            if isinstance(ref, PywinautoElement):
                return ref.control.exists()
            spec = self._window_spec(window)
            kwargs: dict[str, Any] = {}
            if ref.automation_id:
                kwargs["auto_id"] = ref.automation_id
            if ref.title:
                kwargs["title"] = ref.title
            if ref.class_name:
                kwargs["class_name"] = ref.class_name
            if ref.control_type:
                kwargs["control_type"] = ref.control_type
            if ref.best_match:
                kwargs["best_match"] = ref.best_match
            return spec.child_window(**kwargs).exists(timeout=0)
        except Exception:
            return False

    def is_enabled(
        self,
        target: str | ElementRef | PywinautoElement,
        window: PywinautoWindow | None = None,
    ) -> bool:
        try:
            return self.resolve(target, window).is_enabled()
        except Exception:
            return False

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
            import win32gui
            import win32con

            hwnd = window.native_handle
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
        except Exception as exc:
            raise DriverError(str(exc)) from exc

    def bind_uimap(self, uimap: UIMap) -> None:
        self._uimap = uimap
