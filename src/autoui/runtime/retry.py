"""RetryPolicy — только для postconditions (expect)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RetryPolicy:
    """Повторы проверки expect после action."""

    retries: int = 3
    delay: float = 1.0
