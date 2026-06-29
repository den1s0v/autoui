"""
WatcherManager — фоновые наблюдатели внезапных диалогов.

Периодически проверяет when; при срабатывании выполняет action.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from autoui.abstractions.action import IAction
    from autoui.abstractions.condition import ICondition
    from autoui.abstractions.driver import IDriver
    from autoui.core.context import ExecutionContext
    from autoui.core.events import EventBus


@dataclass
class Watcher:
    """Один фоновый наблюдатель."""

    name: str
    when: list
    action: object
    priority: int = 0
    interval: float = 0.5


class WatcherManager:
    def __init__(
        self,
        watchers: list[Watcher],
        ctx: ExecutionContext,
        driver: IDriver,
        event_bus: EventBus,
    ) -> None:
        self._watchers = sorted(watchers, key=lambda w: -w.priority)
        self._ctx = ctx
        self._driver = driver
        self._event_bus = event_bus
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def _loop(self) -> None:
        while not self._stop.is_set():
            if self._ctx.automation_active:
                time.sleep(0.1)
                continue
            for watcher in self._watchers:
                if all(c.check(self._ctx, self._driver) for c in watcher.when):
                    self._ctx.automation_active = True
                    try:
                        watcher.action.execute(self._ctx, self._driver)  # type: ignore[union-attr]
                    finally:
                        self._ctx.automation_active = False
                    break
            time.sleep(0.5)

    def start(self) -> None:
        if not self._watchers:
            return
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)
