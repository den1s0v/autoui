"""
ICondition — проверка для when (preconditions) и expect (postconditions).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from autoui.abstractions.driver import IDriver
    from autoui.core.context import ExecutionContext


class ICondition(Protocol):
    def check(self, ctx: ExecutionContext, driver: IDriver) -> bool: ...
