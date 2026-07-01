"""
PywinautoElementTree — IElementTree над pywinauto control.

Только в drivers/; ядро не импортирует pywinauto.
"""

from __future__ import annotations

from typing import Any

from autoui.abstractions.element_tree import ElementProperties, IElementTree


class PywinautoElementTree(IElementTree):
    def children(self, node: Any) -> list[Any]:
        try:
            info = node.element_info
            return list(info.children())
        except Exception:
            return list(node.children())

    def descendants(self, node: Any) -> list[Any]:
        try:
            return list(node.descendants())
        except Exception:
            out: list[Any] = []

            def walk(ctrl: Any) -> None:
                for child in self.children(ctrl):
                    out.append(child)
                    walk(child)

            walk(node)
            return out

    def properties(self, node: Any) -> ElementProperties:
        try:
            info = node.element_info
            name = info.name or None
            automation_id = getattr(info, "automation_id", None) or None
            class_name = info.class_name or None
            control_type = _control_type_name(info)
            enabled = _safe_bool(lambda: node.is_enabled())
            visible = _safe_bool(lambda: node.is_visible())
        except Exception:
            name = _safe_str(lambda: node.window_text())
            automation_id = None
            class_name = None
            control_type = None
            enabled = None
            visible = None
        return ElementProperties(
            name=name,
            automation_id=automation_id,
            class_name=class_name,
            control_type=control_type,
            enabled=enabled,
            visible=visible,
        )


def _control_type_name(info: Any) -> str | None:
    try:
        ct = info.control_type
        if ct is None:
            return None
        return str(ct)
    except Exception:
        return None


def _safe_bool(fn: Any) -> bool | None:
    try:
        return bool(fn())
    except Exception:
        return None


def _safe_str(fn: Any) -> str | None:
    try:
        val = fn()
        return val if val else None
    except Exception:
        return None
