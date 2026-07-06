"""
IElementTree — примитивы обхода UI-дерева для LocatorExecutor.

Драйверы реализуют Protocol; ядро и locators/ не знают pywinauto.
См. README.md — UIMap / Locator.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable

TreeNode = Any

# Свойства узла для фильтрации: открытый словарь (ключи зависят от драйвера).
ElementProperties = dict[str, Any]


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
