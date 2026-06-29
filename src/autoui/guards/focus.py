"""Опциональный мониторинг foreground window."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FocusPolicy:
    """Включается через CoexistencePolicy.focus_monitor."""

    restore_after_sec: float | None = 30.0
