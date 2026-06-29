"""
PreconditionPolicy — поведение при невыполнении when.

Отдельно от RetryPolicy и PostconditionRecovery (они для expect).
См. README.md — PreconditionOutcome.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from autoui.core.enums import PreconditionMode, PreconditionOutcome

if TYPE_CHECKING:
    from autoui.abstractions.driver import IDriver
    from autoui.core.context import ExecutionContext

# Callback решает исход после таймаута WAIT или в сложных кейсах.
PreconditionResolver = Callable[
    ["ExecutionContext", "IDriver", object],
    PreconditionOutcome,
]


@dataclass
class PreconditionPolicy:
    """
    Политика для фазы when.

    mode=skip: при первой неудаче when — SKIPPED без action.
    mode=required: короткий retry, затем fail.
    """

    mode: PreconditionMode = "required"
    poll_interval: float = 0.5
    wait_timeout: float | None = 30.0
    required_retries: int = 3
    required_delay: float = 0.5
    on_timeout: PreconditionOutcome | PreconditionResolver = "fail"
    goto_step: str | None = None

    def resolve_on_timeout(
        self,
        ctx: ExecutionContext,
        driver: object,
        step: object,
    ) -> PreconditionOutcome:
        """Вычислить исход: константа или вызов callback."""
        if callable(self.on_timeout):
            return self.on_timeout(ctx, driver, step)  # type: ignore[arg-type]
        return self.on_timeout
