"""
PywinautoElementTree — IElementTree над pywinauto control.

properties(): сначала element_info, затем get_properties() (setdefault).
FindDescendants делегирует exact scalar-фильтры в control.descendants(**kwargs) где возможно.
"""

from __future__ import annotations

from typing import Any

from autoui.abstractions.element_tree import ElementProperties, IElementTree
from autoui.locators.matching import is_exact_scalar_condition, match_where
from autoui.locators.ops import FilterWhere
import contextlib

_NATIVE_WHERE_KEYS = frozenset({"class_name", "control_type", "name", "title", "automation_id"})

_ELEMENT_INFO_ATTRS = (
    "name",
    "rich_text",
    "class_name",
    "automation_id",
    "control_type",
    "control_id",
    "handle",
    "process_id",
    "framework_id",
)


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
                    if match_where(self.properties(item), _native_where_as_filter(native))
                ]
        wrapped = _wrap_children(node, raw)
        if post:
            wrapped = [item for item in wrapped if match_where(self.properties(item), post)]
        return wrapped

    def properties(self, node: Any) -> ElementProperties:
        props: ElementProperties = {}
        with contextlib.suppress(Exception):
            props.update(_collect_element_info_props(node.element_info))
        if "name" not in props:
            fallback_name = _safe_str(lambda: node.window_text())
            if fallback_name is not None:
                props["name"] = fallback_name
        if "enabled" not in props:
            enabled = _safe_bool(lambda: node.is_enabled())
            if enabled is not None:
                props["enabled"] = enabled
        if "visible" not in props:
            visible = _safe_bool(lambda: node.is_visible())
            if visible is not None:
                props["visible"] = visible
        try:
            for key, val in node.get_properties().items():
                props.setdefault(key, val)
        except Exception:
            pass
        return props

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


def _collect_element_info_props(ei: Any) -> ElementProperties:
    props: ElementProperties = {}
    for attr in _ELEMENT_INFO_ATTRS:
        if not hasattr(ei, attr):
            continue
        try:
            val = getattr(ei, attr)
        except Exception:
            continue
        props[attr] = _normalize_prop_value(attr, val)
    return props


def _normalize_prop_value(attr: str, val: Any) -> Any:
    if val is None:
        return None
    if attr == "control_type":
        return str(val)
    if isinstance(val, str):
        return val if val else None
    return val


def _native_where_as_filter(native: dict[str, Any]) -> FilterWhere:
    """Ключи pywinauto descendants → ключи properties для match_where."""
    out: FilterWhere = {}
    for key, val in native.items():
        out["name" if key == "title" else key] = val
    return out


def _split_where(where: FilterWhere | None) -> tuple[dict[str, Any], FilterWhere]:
    if not where:
        return {}, {}
    native: dict[str, Any] = {}
    post: FilterWhere = {}
    for key, value in where.items():
        if key in _NATIVE_WHERE_KEYS and is_exact_scalar_condition(value):
            native[_to_pywinauto_key(key)] = value
        else:
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
