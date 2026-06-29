"""Сценарий — граф именованных IStep."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from autoui.abstractions.step import IStep
from autoui.uimap.map import UIMap

if TYPE_CHECKING:
    from autoui.guards.coexistence import CoexistencePolicy
    from autoui.watchers.manager import Watcher


@dataclass
class Scenario:
    """
    Декларативное описание прогона.

    steps — словарь по имени; entry — стартовый шаг.
    order — линейный порядок для перехода когда on_success=None.
    """

    name: str
    entry: str
    steps: dict[str, IStep]
    uimap: UIMap
    order: list[str] | None = None
    watchers: list = field(default_factory=list)
    coexistence: object = field(default_factory=lambda: _default_coexistence())
    app_selector: str | int | None = None
    primary_window_title: str | None = None

    def validate(self) -> None:
        from autoui.core.exceptions import ScenarioError

        if self.entry not in self.steps:
            raise ScenarioError(f"entry step '{self.entry}' not in steps")
        for name, step in self.steps.items():
            if step.name != name:
                raise ScenarioError(f"step key '{name}' != step.name '{step.name}'")

    def next_linear(self, current: str) -> str | None:
        """Следующий шаг в order после current."""
        order = self.order or list(self.steps.keys())
        try:
            idx = order.index(current)
        except ValueError:
            return None
        if idx + 1 < len(order):
            return order[idx + 1]
        return None


def _default_coexistence():
    from autoui.guards.coexistence import CoexistencePolicy

    return CoexistencePolicy()
