"""Проверка StepPipeline без UI (mock driver)."""

from __future__ import annotations

from autoui.conditions.builtin import WindowExists
from autoui.core.context import ExecutionContext
from autoui.core.enums import StepResultKind
from autoui.runtime.pipeline import StepPipeline
from autoui.runtime.precondition import PreconditionPolicy
from autoui.uimap.map import UIMap


class MockDriver:
    def window_exists(self, title: str, app=None) -> bool:
        return title == "Present"

    def exists(self, target, window=None) -> bool:
        return True

    def wait(self, t: float) -> None:
        pass


def test_skip_precondition():
    pipeline = StepPipeline()
    ctx = ExecutionContext(uimap=UIMap())
    policy = PreconditionPolicy(mode="skip")
    result = pipeline.evaluate_when(
        "s",
        [WindowExists("Missing")],
        policy,
        ctx,
        MockDriver(),  # type: ignore[arg-type]
        object(),
    )
    assert result.kind == StepResultKind.SKIPPED


def test_when_met():
    pipeline = StepPipeline()
    ctx = ExecutionContext(uimap=UIMap())
    result = pipeline.evaluate_when(
        "s",
        [WindowExists("Present")],
        PreconditionPolicy(),
        ctx,
        MockDriver(),  # type: ignore[arg-type]
        object(),
    )
    assert result.kind == StepResultKind.SUCCESS


if __name__ == "__main__":
    test_skip_precondition()
    test_when_met()
    print("ok")
