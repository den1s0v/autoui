"""
IElementTree — примитивы обхода UI-дерева для LocatorExecutor.

Драйверы реализуют Protocol; ядро и locators/ не знают pywinauto.
См. README.md — UIMap / Locator.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, runtime_checkable

TreeNode = Any


@dataclass(frozen=True)
class ElementProperties:
    """Свойства узла для фильтрации в pipeline."""

    name: str | None = None
    automation_id: str | None = None
    class_name: str | None = None
    control_type: str | None = None
    enabled: bool | None = None
    visible: bool | None = None


@runtime_checkable
class IElementTree(Protocol):
    """
    Детерминированный порядок children/descendants — контракт для Take(index).
    """

    def children(self, node: TreeNode) -> list[TreeNode]: ...

    def descendants(
        self,
        node: TreeNode,
        *,
        where: Mapping[str, Any] | None = None,
        depth: int | None = None,
    ) -> list[TreeNode]: ...

    def properties(self, node: TreeNode) -> ElementProperties: ...
