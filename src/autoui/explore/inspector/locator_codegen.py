"""
Генерация и разбор Python-кода Locator для Control Inspector.

Dev-tool слой explore; ядро locators не импортирует этот модуль.
"""

from __future__ import annotations

import ast
from typing import Any

from autoui.explore.inspector.hierarchy_navigator import PathSegment
from autoui.locators.errors import LocatorError
from autoui.locators.locator import Locator
from autoui.locators.ops import ChildOp, FilterOp, FindDescendantsOp, LocatorOp, TakeOp

_EVAL_NAMESPACE: dict[str, Any] = {
    "Locator": Locator,
    "ChildOp": ChildOp,
    "FindDescendantsOp": FindDescendantsOp,
    "FilterOp": FilterOp,
    "TakeOp": TakeOp,
}


def locator_from_control_segments(segments: list[PathSegment]) -> Locator:
    """Locator из control-сегментов path (после окна)."""
    ops: list[LocatorOp] = [ChildOp(seg.child_index) for seg in segments]
    return Locator(tuple(ops))


def locator_to_python(
    locator: Locator,
    *,
    window_comment: str | None = None,
    op_comments: list[str] | None = None,
) -> str:
    """Сериализация Locator в исполняемый Python-фрагмент."""
    lines = [
        "from autoui.locators import Locator, ChildOp",
        "",
    ]
    if window_comment:
        lines.append(f"# Window: {window_comment}")
    lines.append("Locator([")
    for i, op in enumerate(locator.ops):
        comment = ""
        if op_comments and i < len(op_comments):
            comment = f"  # {op_comments[i]}"
        if isinstance(op, ChildOp):
            lines.append(f"    ChildOp({op.index}),{comment}")
        elif isinstance(op, FindDescendantsOp):
            where_repr = repr(dict(op.where))
            depth = f", depth={op.depth}" if op.depth is not None else ""
            limit = f", limit={op.limit}" if op.limit is not None else ""
            lines.append(
                f"    FindDescendantsOp(where={where_repr}{depth}{limit}),{comment}"
            )
        elif isinstance(op, FilterOp):
            lines.append(f"    FilterOp(where={repr(dict(op.where))}),{comment}")
        elif isinstance(op, TakeOp):
            lines.append(f"    TakeOp({op.index}),{comment}")
        else:
            raise LocatorError(f"Unsupported op for codegen: {type(op)!r}")
    lines.append("])")
    return "\n".join(lines)


def codegen_from_navigator(
    control_segments: list[PathSegment],
    window_segment: PathSegment | None,
) -> str:
    """Полный текст селектора для панели Generated."""
    if window_segment is None:
        return "# Select a window from Desktop hierarchy first\n"
    if not control_segments:
        return f"# Window: {window_segment.label}\nLocator([])"
    locator = locator_from_control_segments(control_segments)
    window_comment = window_segment.label if window_segment else None
    comments = [seg.label for seg in control_segments]
    return locator_to_python(
        locator,
        window_comment=window_comment,
        op_comments=comments,
    )


def parse_locator_python(text: str) -> Locator:
    """
    Разбор Python-фрагмента Locator через ast + whitelist eval.

    Принимает текст с import или только выражение Locator([...]).
    """
    stripped = text.strip()
    if not stripped:
        raise LocatorError("Empty locator text")

    tree = ast.parse(stripped, mode="exec")
    expr: ast.expr | None = None
    for node in tree.body:
        if isinstance(node, ast.Expr):
            expr = node.value
            break
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            expr = node.value
            break
    if expr is None:
        raise LocatorError("Expected Locator([...]) expression")

    code = compile(ast.Expression(expr), "<locator>", "eval")
    result = eval(code, {"__builtins__": {}}, _EVAL_NAMESPACE)
    if not isinstance(result, Locator):
        raise LocatorError(f"Expression did not evaluate to Locator, got {type(result)!r}")
    return result
