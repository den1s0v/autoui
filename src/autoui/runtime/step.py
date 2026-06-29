"""
Реализации IStep: ActionStep, ProbeStep, BranchStep.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from autoui.abstractions.step import IStep, StepResult
from autoui.core.enums import StepResultKind
from autoui.runtime.precondition import PreconditionPolicy
from autoui.runtime.recovery import PostconditionRecovery
from autoui.runtime.retry import RetryPolicy

if TYPE_CHECKING:
    from autoui.abstractions.action import IAction
    from autoui.abstractions.condition import ICondition
    from autoui.abstractions.driver import IDriver
    from autoui.core.context import ExecutionContext
    from autoui.runtime.pipeline import StepPipeline


@dataclass
class ActionStep:
    """
    Основной шаг: when → action → expect.

    on_success — имя следующего шага; None — линейный порядок в runner.
    """

    name: str
    action: IAction | None = None
    when: list[ICondition] = field(default_factory=list)
    expect: list[ICondition] = field(default_factory=list)
    precondition_policy: PreconditionPolicy = field(default_factory=PreconditionPolicy)
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    postcondition_recovery: PostconditionRecovery | None = None
    on_success: str | None = None
    idempotent: bool = True

    def execute(
        self,
        pipeline: StepPipeline,
        ctx: ExecutionContext,
        driver: IDriver,
    ) -> StepResult:
        ctx.current_step_name = self.name

        # --- when ---
        when_result = pipeline.evaluate_when(
            self.name, self.when, self.precondition_policy, ctx, driver, self
        )
        if when_result.kind == StepResultKind.SKIPPED:
            return StepResult(
                kind=StepResultKind.SKIPPED,
                next_step=self.on_success,
            )
        if when_result.kind == StepResultKind.GOTO:
            return when_result
        if when_result.kind == StepResultKind.FAILED:
            return when_result

        # --- action ---
        pipeline.run_action(self.action, ctx, driver)

        # --- expect ---
        expect_result = pipeline.evaluate_expect(
            self.name,
            self.expect,
            self.retry,
            self.postcondition_recovery,
            ctx,
            driver,
        )
        if expect_result.next_step == "__retry_step__":
            return self.execute(pipeline, ctx, driver)

        if expect_result.kind != StepResultKind.SUCCESS:
            return expect_result

        return StepResult(kind=StepResultKind.SUCCESS, next_step=self.on_success)


@dataclass
class ProbeStep(ActionStep):
    """
    Шаг без action: ждёт when, затем переход on_met.

    action принудительно None.
    """

    on_met: str | None = None

    def __post_init__(self) -> None:
        self.action = None

    def execute(
        self,
        pipeline: StepPipeline,
        ctx: ExecutionContext,
        driver: IDriver,
    ) -> StepResult:
        ctx.current_step_name = self.name
        when_result = pipeline.evaluate_when(
            self.name, self.when, self.precondition_policy, ctx, driver, self
        )
        if when_result.kind == StepResultKind.SKIPPED:
            return StepResult(kind=StepResultKind.SKIPPED, next_step=self.on_success)
        if when_result.kind == StepResultKind.GOTO:
            return when_result
        if when_result.kind == StepResultKind.FAILED:
            return when_result
        if when_result.kind == StepResultKind.SUCCESS and self.when:
            target = self.on_met or self.on_success
            if target:
                return StepResult(kind=StepResultKind.GOTO, next_step=target)
        return StepResult(kind=StepResultKind.SUCCESS, next_step=self.on_success)


@dataclass
class BranchStep:
    """
    Условная ветка: when выполнены → then_steps по порядку; иначе else_goto.
    """

    name: str
    when: list[ICondition] = field(default_factory=list)
    then_steps: list[IStep] = field(default_factory=list)
    else_goto: str | None = None

    def execute(
        self,
        pipeline: StepPipeline,
        ctx: ExecutionContext,
        driver: IDriver,
    ) -> StepResult:
        ctx.current_step_name = self.name
        if pipeline._check_all(self.when, ctx, driver):
            for sub in self.then_steps:
                result = sub.execute(pipeline, ctx, driver)
                if result.kind != StepResultKind.SUCCESS:
                    return result
                if result.next_step:
                    return result
            return StepResult(kind=StepResultKind.SUCCESS)
        if self.else_goto:
            return StepResult(kind=StepResultKind.GOTO, next_step=self.else_goto)
        return StepResult(kind=StepResultKind.SKIPPED)
