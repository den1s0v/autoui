"""Control Inspector — PySide6 GUI для подбора Locator."""

from __future__ import annotations

__all__ = ["run_inspector"]


def run_inspector() -> None:
    from autoui.explore.inspector.app import run_inspector as _run

    _run()
