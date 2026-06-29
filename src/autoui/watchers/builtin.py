"""Примеры watchers для optional dialogs."""

from __future__ import annotations

from autoui.actions.builtin import ClickAction
from autoui.conditions.builtin import WindowExists
from autoui.watchers.manager import Watcher


def license_dialog_watcher(license_ok_key: str = "license_ok") -> Watcher:
    """Закрыть окно лицензии если всплыло во время другого шага."""
    return Watcher(
        name="license_popup",
        when=[WindowExists("Лицензия")],
        action=ClickAction(license_ok_key),
        priority=10,
    )


def error_dialog_watcher(error_ok_key: str = "error_ok") -> Watcher:
    return Watcher(
        name="error_popup",
        when=[WindowExists("Ошибка")],
        action=ClickAction(error_ok_key),
        priority=5,
    )
