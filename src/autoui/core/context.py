"""
Глобальное состояние выполнения сценария.

Хранит variables, текущий шаг, primary window для CoexistenceGuard,
флаг automation_active для фильтрации mouse hook.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from autoui.uimap.map import UIMap


@dataclass
class ExecutionContext:
    """
    Контекст одного прогона сценария.

    variables — данные сценария (пути экспорта, извлечённый текст ошибки).
    automation_active — True пока driver выполняет action от имени агента.
    """

    uimap: UIMap
    variables: dict[str, Any] = field(default_factory=dict)
    run_id: str = field(default_factory=lambda: uuid4().hex)
    current_step_name: str | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    target_window: Any = None  # WindowHandle | None — Any чтобы core не зависел от driver
    primary_app: Any = None
    automation_active: bool = False
    event_bus: Any = None  # EventBus, заполняется runner

    def __getitem__(self, key: str) -> Any:
        return self.variables[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.variables[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.variables.get(key, default)
