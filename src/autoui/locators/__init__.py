"""
Locator Engine — pipeline поиска UI-элементов.

execute() — один узел для сценариев; execute_all() — полное множество для отладки.
Независим от pywinauto; выполняется через IElementTree.
См. README.md — UIMap / Locator.
"""

from autoui.locators.element_set import ElementSet
from autoui.locators.errors import LocatorError, LocatorFilterError, LocatorNotFoundError
from autoui.locators.executor import ExecuteAllResult, ExecuteResult, LocatorExecutor
from autoui.locators.locator import Locator
from autoui.locators.ops import ChildOp, FilterOp, FindDescendantsOp, LocatorOp, TakeOp
from autoui.locators.serde import (
    locator_from_dict,
    locator_from_json,
    locator_to_dict,
    locator_to_json,
)
from autoui.locators.trace import LocatorTrace, TraceStep

__all__ = [
    "ChildOp",
    "ElementSet",
    "ExecuteAllResult",
    "ExecuteResult",
    "FilterOp",
    "FindDescendantsOp",
    "Locator",
    "LocatorError",
    "LocatorFilterError",
    "LocatorExecutor",
    "LocatorNotFoundError",
    "LocatorOp",
    "LocatorTrace",
    "TakeOp",
    "TraceStep",
    "locator_from_dict",
    "locator_from_json",
    "locator_to_dict",
    "locator_to_json",
]
