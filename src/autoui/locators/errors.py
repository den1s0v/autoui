"""Исключения слоя локаторов."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from autoui.locators.trace import LocatorTrace


class LocatorError(Exception):
    """Невалидный locator, op или serde."""


class LocatorNotFoundError(LocatorError):
    """Элемент не найден на одном из шагов pipeline."""

    def __init__(self, message: str, *, trace: LocatorTrace) -> None:
        super().__init__(message)
        self.trace = trace


class LocatorFilterError(LocatorError):
    """Невалидный синтаксис where при создании locator/op."""
