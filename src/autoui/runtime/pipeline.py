"""
StepPipeline — общая логика when / action / expect для ActionStep.

Runner и BranchStep делегируют сюда фазы; политики описаны в README.md.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from autoui.abstractions.step import StepResult
from autoui.core.enums import StepResultKind
from autoui.core.events import GotoStep, RetryStarted, StepSkipped
from autoui.runtime.precondition import PreconditionPolicy

if TYPE_CHECKING:
    from autoui.abstractions.action import IAction
    from autoui.abstractions.condition import ICondition
    from autoui.abstractions.driver import IDriver
    from autoui.core.context import ExecutionContext
    from autoui.runtime.recovery import PostconditionRecovery
    from autoui.runtime.retry import RetryPolicy


class StepPipeline:
    """Вспомогательный объект с фазами выполнения ActionStep."""

    def __init__(self, runner: object | None = None) -> None:
        self._runner = runner

    def _emit(self, ctx: ExecutionContext, event: object) -> None:
        if ctx.event_bus is not None:
            ctx.event_bus.emit(event)

    def _check_all(
        self,
        conditions: list[ICondition],
        ctx: ExecutionContext,
        driver: IDriver,
    ) -> bool:
        return all(c.check(ctx, driver) for c in conditions)

    def _apply_precondition_outcome(
        self,
        outcome: str,
        step_name: str,
        policy: PreconditionPolicy,
        ctx: ExecutionContext,
    ) -> StepResult:
        if outcome == "proceed":
            return StepResult(kind=StepResultKind.SUCCESS)
        if outcome == "skip":
            self._emit(ctx, StepSkipped(step_name))
            return StepResult(kind=StepResultKind.SKIPPED, next_step=None)
        if outcome == "goto":
            target = policy.goto_step
            if not target:
                return StepResult(
                    kind=StepResultKind.FAILED,
                    error_message="goto without goto_step",
                )
            self._emit(ctx, GotoStep(step_name, target))
            return StepResult(kind=StepResultKind.GOTO, next_step=target)
        if outcome == "retry_wait":
            return StepResult(kind=StepResultKind.SUCCESS, next_step="__retry_wait__")
        return StepResult(
            kind=StepResultKind.FAILED,
            error_message=f"precondition outcome: {outcome}",
        )

    def evaluate_when(
        self,
        step_name: str,
        when: list[ICondition],
        policy: PreconditionPolicy,
        ctx: ExecutionContext,
        driver: IDriver,
        step: object,
    ) -> StepResult:
        """
        Фаза when с учётом PreconditionPolicy.

        Возвращает SUCCESS (можно к action), SKIPPED, GOTO или FAILED.
        """

        def met() -> bool:
            if not when:
                return True
            return self._check_all(when, ctx, driver)

        # --- Уже выполнено ---
        if met():
            return StepResult(kind=StepResultKind.SUCCESS)

        # --- mode=skip: опциональный шаг ---
        if policy.mode == "skip":
            self._emit(ctx, StepSkipped(step_name))
            return StepResult(kind=StepResultKind.SKIPPED)

        # --- mode=wait: poll до timeout ---
        if policy.mode == "wait":
            deadline = time.monotonic() + (policy.wait_timeout or 30.0)
            while time.monotonic() < deadline:
                if self._runner and hasattr(self._runner, "check_pause"):
                    self._runner.check_pause()  # type: ignore[union-attr]
                if met():
                    return StepResult(kind=StepResultKind.SUCCESS)
                time.sleep(policy.poll_interval)
            outcome = policy.resolve_on_timeout(ctx, driver, step)
            return self._apply_precondition_outcome(outcome, step_name, policy, ctx)

        # --- mode=required: retry затем fail ---
        for attempt in range(1, policy.required_retries + 1):
            if self._runner and hasattr(self._runner, "check_pause"):
                self._runner.check_pause()  # type: ignore[union-attr]
            if met():
                return StepResult(kind=StepResultKind.SUCCESS)
            self._emit(ctx, RetryStarted(step_name, "when", attempt))
            time.sleep(policy.required_delay)

        return StepResult(
            kind=StepResultKind.FAILED,
            error_message="required preconditions not met",
        )

    def run_action(
        self,
        action: IAction | None,
        ctx: ExecutionContext,
        driver: IDriver,
    ) -> None:
        if action is None:
            return
        ctx.automation_active = True
        try:
            action.execute(ctx, driver)
        finally:
            ctx.automation_active = False

    def evaluate_expect(
        self,
        step_name: str,
        expect: list[ICondition],
        retry: RetryPolicy,
        recovery: PostconditionRecovery | None,
        ctx: ExecutionContext,
        driver: IDriver,
    ) -> StepResult:
        """Фаза expect с RetryPolicy и PostconditionRecovery."""

        if not expect:
            return StepResult(kind=StepResultKind.SUCCESS)

        attempts = retry.retries + 1
        for attempt in range(1, attempts + 1):
            if self._runner and hasattr(self._runner, "check_pause"):
                self._runner.check_pause()  # type: ignore[union-attr]
            if self._check_all(expect, ctx, driver):
                return StepResult(kind=StepResultKind.SUCCESS)
            if attempt < attempts:
                self._emit(ctx, RetryStarted(step_name, "expect", attempt))
                time.sleep(retry.delay)

        if recovery is None:
            return StepResult(
                kind=StepResultKind.FAILED,
                error_message="postconditions not met",
            )

        if recovery.action is not None:
            ctx.automation_active = True
            try:
                recovery.action.execute(ctx, driver)
            finally:
                ctx.automation_active = False

        if recovery.then == "retry_step":
            return StepResult(kind=StepResultKind.SUCCESS, next_step="__retry_step__")
        if recovery.then == "skip":
            self._emit(ctx, StepSkipped(step_name))
            return StepResult(kind=StepResultKind.SKIPPED)
        if recovery.then == "goto" and recovery.goto_step:
            self._emit(ctx, GotoStep(step_name, recovery.goto_step))
            return StepResult(kind=StepResultKind.GOTO, next_step=recovery.goto_step)
        return StepResult(
            kind=StepResultKind.FAILED,
            error_message="postcondition recovery exhausted",
        )
