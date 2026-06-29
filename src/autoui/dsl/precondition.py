"""Фабрики PreconditionPolicy."""

from __future__ import annotations

from autoui.runtime.precondition import PreconditionPolicy


def skip_if_not_met() -> PreconditionPolicy:
    """Опциональный шаг: when не выполнены → SKIPPED."""
    return PreconditionPolicy(mode="skip")


def wait_until(
    timeout: float = 30.0,
    on_timeout: str = "fail",
    goto_step: str | None = None,
    poll_interval: float = 0.5,
) -> PreconditionPolicy:
    """Ждать when до timeout; затем on_timeout outcome."""
    return PreconditionPolicy(
        mode="wait",
        wait_timeout=timeout,
        on_timeout=on_timeout,  # type: ignore[arg-type]
        goto_step=goto_step,
        poll_interval=poll_interval,
    )
