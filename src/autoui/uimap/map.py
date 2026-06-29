"""
UIMap — реестр логическое_имя → ElementRef.

При обновлении приложения меняется только map, не шаги сценария.
"""

from __future__ import annotations

from typing import Mapping

from autoui.core.exceptions import AutoUIError
from autoui.uimap.element_ref import ElementRef


class UIMap:
    """Именованный словарь локаторов с resolve по ключу."""

    def __init__(self, elements: Mapping[str, ElementRef | dict] | None = None) -> None:
        self._elements: dict[str, ElementRef] = {}
        if elements:
            for key, value in elements.items():
                if isinstance(value, ElementRef):
                    self._elements[key] = value
                elif isinstance(value, dict):
                    self._elements[key] = ElementRef(**value)
                else:
                    raise AutoUIError(f"Invalid element spec for '{key}'")

    def resolve(self, key: str) -> ElementRef:
        if key not in self._elements:
            raise AutoUIError(f"UIMap: unknown key '{key}'")
        return self._elements[key]

    def register(self, key: str, ref: ElementRef) -> None:
        self._elements[key] = ref

    def keys(self) -> list[str]:
        return list(self._elements.keys())
