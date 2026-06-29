"""
Шина событий — слабая связь runner с журналом, GUI (будущим), guard.

Runner только emit; подписчики не влияют на логику шагов.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class BeforeStep:
    step_name: str


@dataclass
class AfterStep:
    step_name: str
    result: str


@dataclass
class StepSkipped:
    step_name: str


@dataclass
class RetryStarted:
    step_name: str
    phase: str  # "when" | "expect"
    attempt: int


@dataclass
class GotoStep:
    from_step: str
    to_step: str


@dataclass
class UserActivityDetected:
    pass


@dataclass
class UserIdle:
    pass


@dataclass
class FocusLost:
    pass


@dataclass
class FocusRestored:
    pass


@dataclass
class Paused:
    reason: str


@dataclass
class Error:
    step_name: str
    message: str


@dataclass
class Finished:
    pass


Event = Any
Listener = Callable[[Event], None]


class EventBus:
    """Простой sync pub/sub для одного потока runner."""

    def __init__(self) -> None:
        self._listeners: list[Listener] = []

    def subscribe(self, listener: Listener) -> None:
        self._listeners.append(listener)

    def emit(self, event: Event) -> None:
        for listener in list(self._listeners):
            listener(event)
