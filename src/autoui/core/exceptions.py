"""
Исключения движка.

StepFailed — шаг не прошёл when/expect и recovery исчерпан.
DriverError — ошибка на уровне драйвера (UIA, окно не найдено).
"""

from __future__ import annotations


class AutoUIError(Exception):
    """Базовое исключение autoUI."""


class StepFailed(AutoUIError):
    """Шаг завершился с ошибкой; runner переходит в ERROR."""

    def __init__(self, step_name: str, message: str) -> None:
        self.step_name = step_name
        super().__init__(f"Step '{step_name}' failed: {message}")


class DriverError(AutoUIError):
    """Ошибка взаимодействия с UI через IDriver."""


class ScenarioError(AutoUIError):
    """Некорректная конфигурация сценария (битые ссылки goto)."""
