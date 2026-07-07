"""
Подписи узлов UI для Control Inspector.

Формат как в ExplorerSession.list_indexed: control_type | name | auto_id.
"""

from __future__ import annotations

from typing import Any

from autoui.drivers.pywinauto_tree import PywinautoElementTree

_tree = PywinautoElementTree()

DESKTOP_LABEL = "Desktop"


def format_control_label(control: Any) -> str:
    """Человекочитаемая подпись pywinauto control."""
    props = _tree.properties(control)
    name = props.get("name") or props.get("rich_text") or ""
    auto_id = props.get("automation_id") or ""
    ct = props.get("control_type") or props.get("friendly_class_name") or ""
    return f"{ct} | {name!r} | auto_id={auto_id!r}"


def format_window_label(control: Any) -> str:
    """Краткая подпись top-level окна."""
    try:
        title = control.window_text() or "<no title>"
    except Exception:
        title = "<no title>"
    props = _tree.properties(control)
    ct = props.get("control_type") or props.get("friendly_class_name") or "Window"
    return f"{ct} | {title!r}"
