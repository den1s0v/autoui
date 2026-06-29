"""
Перечисления состояний runner и исходов шагов/политик.

См. README.md — разделы PreconditionPolicy и AutomationRunner.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

# Исход разрешения preconditions (on_timeout или callback).
PreconditionOutcome = Literal["proceed", "skip", "fail", "goto", "retry_wait"]

# Исход postcondition recovery после провала expect.
PostconditionOutcome = Literal["retry_step", "skip", "goto", "fail"]

# Режим ожидания preconditions.
PreconditionMode = Literal["required", "skip", "wait"]


class RunState(Enum):
    """Состояние AutomationRunner."""

    RUNNING = "running"
    PAUSED = "paused"
    PAUSED_BY_USER = "paused_by_user"
    ERROR = "error"
    FINISHED = "finished"
    STOPPED = "stopped"


class StepResultKind(Enum):
    """Результат выполнения одного IStep для runner."""

    SUCCESS = "success"
    SKIPPED = "skipped"
    GOTO = "goto"
    FAILED = "failed"
