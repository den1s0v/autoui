"""Built-in actions — конфигурации поверх IDriver."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from autoui.abstractions.action import IAction
from autoui.abstractions.driver import IDriver, WindowHandle
from autoui.core.context import ExecutionContext


@dataclass
class ClickAction:
    """Клик по ключу UIMap или Locator."""

    target: str
    window: WindowHandle | None = None

    def execute(self, ctx: ExecutionContext, driver: IDriver) -> None:
        driver.click(self.target, window=self.window)


@dataclass
class SetTextAction:
    target: str
    text: str | None = None
    var: str | None = None
    window: WindowHandle | None = None

    def execute(self, ctx: ExecutionContext, driver: IDriver) -> None:
        value = self.text if self.text is not None else str(ctx[self.var])  # type: ignore[index]
        driver.set_text(self.target, value, window=self.window)


@dataclass
class ReadTextAction:
    """Читает текст элемента в ctx[var]."""

    target: str
    into: str
    window: WindowHandle | None = None

    def execute(self, ctx: ExecutionContext, driver: IDriver) -> None:
        ctx[self.into] = driver.get_text(self.target, window=self.window)


@dataclass
class WaitAction:
    timeout: float

    def execute(self, ctx: ExecutionContext, driver: IDriver) -> None:
        driver.wait(self.timeout)


@dataclass
class ActivateWindowAction:
    window: WindowHandle | None = None

    def execute(self, ctx: ExecutionContext, driver: IDriver) -> None:
        driver.activate_window(self.window)


@dataclass
class PressHotkeyAction:
    keys: Sequence[str]

    def execute(self, ctx: ExecutionContext, driver: IDriver) -> None:
        driver.press_hotkey(*self.keys)


@dataclass
class SequenceAction:
    """Несколько действий подряд."""

    actions: Sequence[IAction]

    def execute(self, ctx: ExecutionContext, driver: IDriver) -> None:
        for action in self.actions:
            action.execute(ctx, driver)


@dataclass
class AppendVarToFileAction:
    path: str
    var: str

    def execute(self, ctx: ExecutionContext, driver: IDriver) -> None:
        from pathlib import Path

        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with Path(self.path).open("a", encoding="utf-8") as f:
            f.write(str(ctx.get(self.var, "")) + "\n")
