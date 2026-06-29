"""
AutomationRunner — синхронная state machine выполнения Scenario.

Интегрирует CoexistenceGuard, WatcherManager, SnapshotStore, EventBus.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any

from autoui.abstractions.driver import IDriver
from autoui.abstractions.step import StepResult
from autoui.core.context import ExecutionContext
from autoui.core.enums import RunState, StepResultKind
from autoui.core.events import AfterStep, BeforeStep, Error, Finished, Paused
from autoui.core.exceptions import StepFailed
from autoui.core.events import EventBus
from autoui.runtime.pipeline import StepPipeline
from autoui.runtime.scenario import Scenario
from autoui.runtime.snapshot import SnapshotStore


@dataclass
class RunResult:
    state: RunState
    run_id: str
    last_step: str | None = None
    error: str | None = None


class AutomationRunner:
    """Движок исполнения; один поток, guard в фоне."""

    def __init__(
        self,
        driver: IDriver,
        event_bus: EventBus | None = None,
        snapshot_store: SnapshotStore | None = None,
    ) -> None:
        self.driver = driver
        self.event_bus = event_bus or EventBus()
        self.snapshots = snapshot_store or SnapshotStore()
        self.pipeline = StepPipeline(runner=self)
        self._state = RunState.RUNNING
        self._pause_event = threading.Event()
        self._pause_event.set()
        self._stop_requested = False
        self._jump_target: str | None = None
        self._coexistence_guard: Any = None
        self._watcher_manager: Any = None

    @property
    def state(self) -> RunState:
        return self._state

    def pause(self) -> None:
        self._state = RunState.PAUSED
        self._pause_event.clear()
        self.event_bus.emit(Paused("manual"))

    def resume(self) -> None:
        if self._state in (RunState.PAUSED, RunState.PAUSED_BY_USER):
            self._state = RunState.RUNNING
            self._pause_event.set()

    def stop(self) -> None:
        self._stop_requested = True
        self._pause_event.set()

    def jump_to(self, step_name: str) -> None:
        """Прыжок при PAUSED/ERROR — применяется на следующей итерации."""
        self._jump_target = step_name

    def check_pause(self) -> None:
        """Блокировка пока PAUSED; вызывается из pipeline и guard."""
        while not self._pause_event.is_set():
            if self._stop_requested:
                return
            time.sleep(0.1)
        if self._stop_requested:
            return

    def _on_user_pause(self) -> None:
        self._state = RunState.PAUSED_BY_USER
        self._pause_event.clear()
        self.event_bus.emit(Paused("user_activity"))

    def _on_user_idle(self) -> None:
        if self._state == RunState.PAUSED_BY_USER:
            self.resume()

    def run(
        self,
        scenario: Scenario,
        variables: dict | None = None,
        start_from: str | None = None,
    ) -> RunResult:
        scenario.validate()
        ctx = ExecutionContext(
            uimap=scenario.uimap,
            variables=dict(variables or {}),
        )
        ctx.event_bus = self.event_bus

        if hasattr(self.driver, "bind_uimap"):
            self.driver.bind_uimap(scenario.uimap)

        if scenario.app_selector is not None:
            app = self.driver.connect_running_app(scenario.app_selector)
            ctx.primary_app = app
            if scenario.primary_window_title:
                win = self.driver.attach_window(app, title=scenario.primary_window_title)
                self.driver.set_primary(app=app, window=win)
                ctx.target_window = win

        from autoui.guards.coexistence import CoexistenceGuard
        from autoui.watchers.manager import WatcherManager

        self._coexistence_guard = CoexistenceGuard(
            self.driver,
            ctx,
            scenario.coexistence,
            self.event_bus,
            on_pause=self._on_user_pause,
            on_idle=self._on_user_idle,
        )
        self._coexistence_guard.start()

        self._watcher_manager = WatcherManager(scenario.watchers, ctx, self.driver, self.event_bus)
        self._watcher_manager.start()

        current = start_from or scenario.entry
        self._state = RunState.RUNNING
        self._stop_requested = False

        try:
            while current and not self._stop_requested:
                if self._jump_target:
                    current = self._jump_target
                    self._jump_target = None

                self.check_pause()
                if self._stop_requested:
                    break

                step = scenario.steps.get(current)
                if step is None:
                    raise StepFailed(current, f"unknown step '{current}'")

                self.event_bus.emit(BeforeStep(current))
                result = step.execute(self.pipeline, ctx, self.driver)
                self.event_bus.emit(AfterStep(current, result.kind.value))

                if result.kind == StepResultKind.FAILED:
                    self._state = RunState.ERROR
                    msg = result.error_message or "failed"
                    self.event_bus.emit(Error(current, msg))
                    return RunResult(RunState.ERROR, ctx.run_id, current, msg)

                if result.kind == StepResultKind.GOTO and result.next_step:
                    current = result.next_step
                    continue

                if result.kind in (StepResultKind.SUCCESS, StepResultKind.SKIPPED):
                    self.snapshots.save(
                        ctx.run_id,
                        scenario.name,
                        current,
                        ctx.variables,
                    )
                    next_name = result.next_step or scenario.next_linear(current)
                    current = next_name
                    continue

            if self._stop_requested:
                self._state = RunState.STOPPED
                return RunResult(RunState.STOPPED, ctx.run_id, ctx.current_step_name)

            self._state = RunState.FINISHED
            self.event_bus.emit(Finished())
            return RunResult(RunState.FINISHED, ctx.run_id, ctx.current_step_name)

        finally:
            if self._coexistence_guard:
                self._coexistence_guard.stop()
            if self._watcher_manager:
                self._watcher_manager.stop()

    def resume_from_snapshot(
        self,
        scenario: Scenario,
        snapshot_path: str,
        variables: dict | None = None,
    ) -> RunResult:
        snap = self.snapshots.load(snapshot_path)
        merged = dict(snap.variables)
        if variables:
            merged.update(variables)
        return self.run(scenario, variables=merged, start_from=snap.current_step_name)
