"""
IStep — общий контракт ActionStep, ProbeStep, BranchStep.

Runner вызывает execute полиморфно; union Step | BranchStep не используется.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from autoui.core.enums import StepResultKind

if TYPE_CHECKING:
    from autoui.abstractions.driver import IDriver
    from autoui.core.context import ExecutionContext
    from autoui.runtime.pipeline import StepPipeline


@dataclass
class StepResult:
    """Исход execute для AutomationRunner."""

    kind: StepResultKind
    next_step: str | None = None
    error_message: str | None = None


class IStep(Protocol):
    name: str

    def execute(
        self,
        pipeline: StepPipeline,
        ctx: ExecutionContext,
        driver: IDriver,
    ) -> StepResult: ...
