"""
Locator Engine — pipeline поиска UI-элементов.

Независим от pywinauto; выполняется через IElementTree.
См. README.md — UIMap / Locator.
"""

from autoui.locators.element_set import ElementSet
from autoui.locators.errors import LocatorError, LocatorNotFoundError
from autoui.locators.executor import ExecuteResult, LocatorExecutor
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
    "ExecuteResult",
    "FilterOp",
    "FindDescendantsOp",
    "Locator",
    "LocatorError",
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
