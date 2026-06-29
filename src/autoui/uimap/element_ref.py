"""
ElementRef — декларативный локатор UI-элемента.

Не интерактивен: только поля для поиска. Резолв в UIElement — через IDriver.
См. README.md — UIMap / ElementRef.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ElementRef:
    """
    Описание «как найти» элемент в окне.

    Несколько полей — fallback для UIA; driver пробует в разумном порядке.
    """

    title: str | None = None
    automation_id: str | None = None
    class_name: str | None = None
    control_type: str | None = None
    best_match: str | None = None

    def is_empty(self) -> bool:
        return not any(
            (
                self.title,
                self.automation_id,
                self.class_name,
                self.control_type,
                self.best_match,
            )
        )
