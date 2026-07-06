"""
PywinautoElementTree — IElementTree над pywinauto control.

Возвращает UIAWrapper (как node.children() в pywinauto), не сырой ElementInfo.
FindDescendants делегирует фильтры и depth в control.descendants(**kwargs) где возможно.
"""

from __future__ import annotations

from typing import Any

from autoui.abstractions.element_tree import ElementProperties, IElementTree
from autoui.locators.ops import FILTER_KEYS, FilterWhere

_NATIVE_WHERE_KEYS = frozenset({"class_name", "control_type", "name", "title"})


class PywinautoElementTree(IElementTree):
    def children(self, node: Any) -> list[Any]:
        try:
            raw = list(node.children())
        except Exception:
            return self._children_fallback(node)
        return _wrap_children(node, raw)

    def descendants(
        self,
        node: Any,
        *,
        where: FilterWhere | None = None,
        depth: int | None = None,
    ) -> list[Any]:
        native, post = _split_where(where)
        try:
            kwargs = dict(native)
            if depth is not None:
                kwargs["depth"] = depth
            raw = list(node.descendants(**kwargs))
        except Exception:
            raw = self._descendants_fallback(node, depth=depth)
            if native:
                raw = [
                    item
                    for item in raw
                    if _matches_native_props(self.properties(item), native)
                ]
        wrapped = _wrap_children(node, raw)
        if post:
            wrapped = [item for item in wrapped if _matches_post(self.properties(item), post)]
        return wrapped

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

    def _children_fallback(self, node: Any) -> list[Any]:
        try:
            info = node.element_info
            raw = list(info.children())
            return _wrap_children(node, raw)
        except Exception:
            return []

    def _descendants_fallback(self, node: Any, *, depth: int | None = None) -> list[Any]:
        out: list[Any] = []

        def walk(ctrl: Any, remaining: int | None) -> None:
            for child in self.children(ctrl):
                out.append(child)
                if remaining is None or remaining > 1:
                    next_depth = None if remaining is None else remaining - 1
                    walk(child, next_depth)

        walk(node, depth)
        return out


def _split_where(where: FilterWhere | None) -> tuple[dict[str, Any], FilterWhere]:
    if not where:
        return {}, {}
    native: dict[str, Any] = {}
    post: FilterWhere = {}
    for key, value in where.items():
        if key in _NATIVE_WHERE_KEYS:
            native[_to_pywinauto_key(key)] = value
        elif key in FILTER_KEYS:
            post[key] = value
    return native, post


def _to_pywinauto_key(key: str) -> str:
    if key == "name":
        return "title"
    return key


def _wrap_children(parent: Any, items: list[Any]) -> list[Any]:
    if not items:
        return items
    if hasattr(items[0], "draw_outline"):
        return items
    backend = getattr(parent, "backend", None)
    if backend is None:
        return items
    return [backend.generic_wrapper_class(item) for item in items]


def _matches_native_props(props: ElementProperties, native: dict[str, Any]) -> bool:
    for key, expected in native.items():
        attr = "name" if key == "title" else key
        if getattr(props, attr, None) != expected:
            return False
    return True


def _matches_post(props: ElementProperties, post: FilterWhere) -> bool:
    for key, expected in post.items():
        if getattr(props, key, None) != expected:
            return False
    return True


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
