"""
Точка входа: python -m autoui.explore.inspector
"""

from __future__ import annotations


def main() -> None:
    try:
        from autoui.explore.inspector.app import run_inspector
    except ImportError as exc:
        raise SystemExit(
            "PySide6 is required for Control Inspector. "
            'Install with: pip install -e ".[explore]"'
        ) from exc
    run_inspector()


if __name__ == "__main__":
    main()
