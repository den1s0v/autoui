"""Structured journal — подписчик EventBus."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from autoui.core.events import (
    AfterStep,
    BeforeStep,
    Error,
    Finished,
    GotoStep,
    RetryStarted,
    StepSkipped,
    UserActivityDetected,
    UserIdle,
)

logger = logging.getLogger("autoui")


class JournalHandler:
    """Пишет события в logging и опционально в файл."""

    def __init__(self, log_file: str | Path | None = None) -> None:
        self._log_file = Path(log_file) if log_file else None
        if self._log_file:
            self._log_file.parent.mkdir(parents=True, exist_ok=True)

    def __call__(self, event: Any) -> None:
        line = self._format(event)
        logger.info(line)
        if self._log_file:
            with self._log_file.open("a", encoding="utf-8") as f:
                f.write(line + "\n")

    def _format(self, event: Any) -> str:
        if isinstance(event, BeforeStep):
            return f"→ step {event.step_name}"
        if isinstance(event, AfterStep):
            return f"← step {event.step_name} ({event.result})"
        if isinstance(event, StepSkipped):
            return f"⊘ skipped {event.step_name}"
        if isinstance(event, RetryStarted):
            return f"↻ retry {event.step_name} [{event.phase}] #{event.attempt}"
        if isinstance(event, GotoStep):
            return f"⇒ goto {event.from_step} → {event.to_step}"
        if isinstance(event, UserActivityDetected):
            return "⏸ user activity — pause"
        if isinstance(event, UserIdle):
            return "▶ user idle — resume"
        if isinstance(event, Error):
            return f"✗ error at {event.step_name}: {event.message}"
        if isinstance(event, Finished):
            return "✓ finished"
        return repr(event)
