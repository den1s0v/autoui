"""
UIMap — реестр логическое_имя → Locator.

При обновлении приложения меняется только map, не шаги сценария.
См. README.md — UIMap / Locator.
"""

from __future__ import annotations

from typing import Mapping

from autoui.core.exceptions import AutoUIError
from autoui.locators.locator import Locator
from autoui.locators.serde import locator_from_dict


class UIMap:
    """Именованный словарь локаторов с resolve по ключу."""

    def __init__(self, elements: Mapping[str, Locator | dict] | None = None) -> None:
        self._elements: dict[str, Locator] = {}
        if elements:
            for key, value in elements.items():
                if isinstance(value, Locator):
                    self._elements[key] = value
                elif isinstance(value, dict):
                    self._elements[key] = locator_from_dict(value)
                else:
                    raise AutoUIError(f"Invalid element spec for '{key}'")

    def resolve(self, key: str) -> Locator:
        if key not in self._elements:
            raise AutoUIError(f"UIMap: unknown key '{key}'")
        return self._elements[key]

    def register(self, key: str, ref: Locator) -> None:
        self._elements[key] = ref

    def keys(self) -> list[str]:
        return list(self._elements.keys())
