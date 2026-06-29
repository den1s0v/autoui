"""
IDriver и opaque-обёртки AppHandle, WindowHandle, UIElement.

Ядро знает только Protocol; PywinautoDriver — в drivers/.
См. README.md — IDriver.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from autoui.uimap.element_ref import ElementRef


@runtime_checkable
class AppHandle(Protocol):
    """Подключённый процесс."""

    @property
    def native_id(self) -> int: ...


@runtime_checkable
class WindowHandle(Protocol):
    """Конкретное окно приложения."""

    @property
    def native_handle(self) -> int: ...


@runtime_checkable
class UIElement(Protocol):
    """Разрешённый элемент — интерактивный объект runtime."""

    def click(self) -> None: ...
    def set_text(self, text: str) -> None: ...
    def get_text(self) -> str: ...
    def get_value(self) -> str: ...
    def is_enabled(self) -> bool: ...


class IDriver(Protocol):
    """
    Контракт драйвера UI.

    window=None во всех методах — primary window из set_primary.
    target может быть str (ключ UIMap), ElementRef или UIElement.
    """

    def connect_running_app(self, selector: str | int) -> AppHandle: ...

    def attach_window(
        self,
        app: AppHandle,
        *,
        title: str | None = None,
        handle: int | None = None,
    ) -> WindowHandle: ...

    def set_primary(
        self,
        app: AppHandle | None = None,
        window: WindowHandle | None = None,
    ) -> None: ...

    def resolve(
        self,
        target: str | ElementRef | UIElement,
        window: WindowHandle | None = None,
    ) -> UIElement: ...

    def click(
        self,
        target: str | ElementRef | UIElement,
        window: WindowHandle | None = None,
    ) -> None: ...

    def set_text(
        self,
        target: str | ElementRef | UIElement,
        text: str,
        window: WindowHandle | None = None,
    ) -> None: ...

    def get_text(
        self,
        target: str | ElementRef | UIElement,
        window: WindowHandle | None = None,
    ) -> str: ...

    def get_value(
        self,
        target: str | ElementRef | UIElement,
        window: WindowHandle | None = None,
    ) -> str: ...

    def check_checkbox(
        self,
        target: str | ElementRef | UIElement,
        checked: bool,
        window: WindowHandle | None = None,
    ) -> None: ...

    def exists(
        self,
        target: str | ElementRef | UIElement,
        window: WindowHandle | None = None,
    ) -> bool: ...

    def is_enabled(
        self,
        target: str | ElementRef | UIElement,
        window: WindowHandle | None = None,
    ) -> bool: ...

    def activate_window(self, window: WindowHandle | None = None) -> None: ...

    def press_hotkey(self, *keys: str) -> None: ...

    def wait(self, timeout: float) -> None: ...

    def window_exists(self, title_substring: str, app: AppHandle | None = None) -> bool: ...

    def get_foreground_window(self) -> WindowHandle | None: ...

    def set_foreground(self, window: WindowHandle) -> None: ...
