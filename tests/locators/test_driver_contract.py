"""Driver contract tests for resolve/exists not-found behavior."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from autoui.abstractions.element_tree import IElementTree
from autoui.core.exceptions import DriverError
from autoui.locators import Locator, LocatorExecutor, LocatorNotFoundError
from autoui.locators.trace import LocatorTrace
from autoui.uimap.map import UIMap
from tests.locators.conftest import MockElementTree, build_sample_tree


@dataclass
class MockUIElement:
  control: Any

  def click(self) -> None:
      pass

  def set_text(self, text: str) -> None:
      pass

  def get_text(self) -> str:
      return ""

  def get_value(self) -> str:
      return ""

  def is_enabled(self) -> bool:
      return True


class MockDriver:
    """Минимальный драйвер с контрактом resolve→None, exists→False."""

    def __init__(self) -> None:
        self._tree = MockElementTree()
        self._root = build_sample_tree()
        self._executor = LocatorExecutor()
        self._trace_hook_calls: list[LocatorTrace] = []

    def _run_locator(self, locator: Locator):
        try:
            return self._executor.execute(self._tree, self._root, locator)
        except LocatorNotFoundError as exc:
            self._trace_hook_calls.append(exc.trace)
            return None

    def resolve(self, target: Locator) -> MockUIElement | None:
        result = self._run_locator(target)
        if result is None:
            return None
        return MockUIElement(control=result.node)

    def exists(self, target: Locator) -> bool:
        return self._run_locator(target) is not None

    def click(self, target: Locator) -> None:
        el = self.resolve(target)
        if el is None:
            raise DriverError(f"Element not found: {target!r}")
        el.click()


def test_mock_driver_resolve_none_on_not_found() -> None:
    driver = MockDriver()
    locator = Locator.find(name="Несуществует")
    assert driver.resolve(locator) is None


def test_mock_driver_exists_false_on_not_found() -> None:
    driver = MockDriver()
    locator = Locator.find(name="Несуществует")
    assert driver.exists(locator) is False


def test_mock_driver_click_raises_driver_error() -> None:
    driver = MockDriver()
    with pytest.raises(DriverError):
        driver.click(Locator.find(name="Несуществует"))


def test_mock_driver_resolve_success() -> None:
    driver = MockDriver()
    el = driver.resolve(Locator.find(name="OK"))
    assert el is not None


from autoui.locators.ops import FindDescendantsOp


def test_uimap_accepts_locator_dict() -> None:
    m = UIMap({"btn": {"find": {"name": "OK"}}})
    loc = m.resolve("btn")
    assert isinstance(loc.ops[0], FindDescendantsOp)
    assert loc.ops[0].where["name"] == "OK"
