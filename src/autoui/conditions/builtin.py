"""Built-in conditions для when и expect."""

from __future__ import annotations

import os
from dataclasses import dataclass

from autoui.abstractions.driver import IDriver
from autoui.core.context import ExecutionContext


@dataclass
class WindowExists:
    """Окно с подстрокой в заголовке существует."""

    title_substring: str

    def check(self, ctx: ExecutionContext, driver: IDriver) -> bool:
        return driver.window_exists(self.title_substring)


@dataclass
class ControlExists:
    target: str

    def check(self, ctx: ExecutionContext, driver: IDriver) -> bool:
        return driver.exists(self.target)


@dataclass
class ControlEnabled:
    target: str

    def check(self, ctx: ExecutionContext, driver: IDriver) -> bool:
        return driver.is_enabled(self.target)


@dataclass
class ControlValueEquals:
    target: str
    value: str

    def check(self, ctx: ExecutionContext, driver: IDriver) -> bool:
        return driver.get_value(self.target) == self.value


@dataclass
class FileExists:
    path: str | None = None
    var: str | None = None

    def check(self, ctx: ExecutionContext, driver: IDriver) -> bool:
        p = self.path or str(ctx.get(self.var, ""))
        return bool(p) and os.path.isfile(p)


@dataclass
class AllConditions:
    conditions: list

    def check(self, ctx: ExecutionContext, driver: IDriver) -> bool:
        return all(c.check(ctx, driver) for c in self.conditions)
