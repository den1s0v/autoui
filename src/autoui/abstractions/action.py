"""
IAction — выполняемое действие в фазе action шага.

Runner выставляет ctx.automation_active на время execute.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from autoui.abstractions.driver import IDriver
    from autoui.core.context import ExecutionContext


class IAction(Protocol):
    def execute(self, ctx: ExecutionContext, driver: IDriver) -> None: ...
