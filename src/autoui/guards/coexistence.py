"""
CoexistenceGuard — пауза при активности пользователя, auto-resume после idle.

См. README.md — CoexistenceGuard.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Callable

from autoui.core.context import ExecutionContext
from autoui.core.events import EventBus, FocusLost, FocusRestored, UserActivityDetected, UserIdle
from autoui.guards.mouse_hook import MouseHook


@dataclass
class CoexistencePolicy:
    mouse_monitor: bool = True
    idle_resume_sec: float = 30.0
    focus_monitor: bool = False
    focus_restore_sec: float | None = 30.0


class CoexistenceGuard:
    """Фоновый поток: mouse hook + опционально focus poll."""

    def __init__(
        self,
        driver: object,
        ctx: ExecutionContext,
        policy: CoexistencePolicy,
        event_bus: EventBus,
        on_pause: Callable[[], None],
        on_idle: Callable[[], None],
    ) -> None:
        self._driver = driver
        self._ctx = ctx
        self._policy = policy
        self._event_bus = event_bus
        self._on_pause = on_pause
        self._on_idle = on_idle
        self._last_activity = time.monotonic()
        self._mouse_hook: MouseHook | None = None
        self._poll_thread: threading.Thread | None = None
        self._stop = threading.Event()

    def _user_activity(self) -> None:
        self._last_activity = time.monotonic()
        self._event_bus.emit(UserActivityDetected())
        self._on_pause()

    def _poll_idle(self) -> None:
        while not self._stop.is_set():
            idle = time.monotonic() - self._last_activity
            if idle >= self._policy.idle_resume_sec:
                self._event_bus.emit(UserIdle())
                self._on_idle()
            if self._policy.focus_monitor and self._ctx.target_window is not None:
                self._check_focus()
            time.sleep(0.5)

    def _check_focus(self) -> None:
        try:
            fg = self._driver.get_foreground_window()
            target = self._ctx.target_window
            if fg is None or target is None:
                return
            if fg.native_handle != target.native_handle:
                self._event_bus.emit(FocusLost())
                self._on_pause()
                if self._policy.focus_restore_sec:
                    time.sleep(self._policy.focus_restore_sec)
                    self._driver.set_foreground(target)
                    self._event_bus.emit(FocusRestored())
        except Exception:
            pass

    def start(self) -> None:
        if self._policy.mouse_monitor:
            self._mouse_hook = MouseHook(
                on_activity=self._user_activity,
                is_automation_active=lambda: self._ctx.automation_active,
            )
            self._mouse_hook.start()
        self._poll_thread = threading.Thread(target=self._poll_idle, daemon=True)
        self._poll_thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._mouse_hook:
            self._mouse_hook.stop()
        if self._poll_thread:
            self._poll_thread.join(timeout=2)
