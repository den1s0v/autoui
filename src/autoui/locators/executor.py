"""
LocatorExecutor — выполнение pipeline над IElementTree.

execute() — один узел для сценариев (с предупреждением при усечении N→1).
execute_all() — полное множество для playground и отладки.
См. README.md — UIMap / Locator.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from autoui.abstractions.element_tree import ElementProperties, IElementTree
from autoui.locators.element_set import ElementSet
from autoui.locators.errors import LocatorNotFoundError
from autoui.locators.locator import Locator
from autoui.locators.ops import (
    ChildOp,
    FilterOp,
    FilterWhere,
    FindDescendantsOp,
    LocatorOp,
    TakeOp,
)
from autoui.locators.trace import LocatorTrace, TraceStatus, TraceStep

TreeNode = Any


@dataclass(frozen=True)
class ExecuteAllResult:
    """
    Результат pipeline без усечения до одного узла.

    Нужен для playground и отладки: FindDescendants без Take возвращает
    всё множество кандидатов, а не только nodes[0].
    """

    nodes: tuple[TreeNode, ...]
    trace: LocatorTrace


@dataclass(frozen=True)
class ExecuteResult:
    """
    Результат pipeline для одного целевого узла (driver.resolve, click).

    truncated_from — исходный размер множества, если execute() взял только
    nodes[0]; None если кандидат был один.
    """

    node: TreeNode
    trace: LocatorTrace
    truncated_from: int | None = None


class LocatorExecutor:
    def execute(self, tree: IElementTree, root: TreeNode, locator: Locator) -> ExecuteResult:
        """
        Выполнить pipeline и вернуть один узел для действий сценария.

        Если после pipeline кандидатов > 1 — берётся nodes[0], в truncated_from
        и trace фиксируется предупреждение (не ошибка, чтобы не ломать цепочки).
        Для полного множества — execute_all().
        """
        current, trace = self._run_pipeline(tree, root, locator)
        if len(current.nodes) > 1:
            return ExecuteResult(
                node=current.nodes[0],
                trace=LocatorTrace(
                    steps=trace.steps,
                    failed_step_index=trace.failed_step_index,
                    failure_reason=trace.failure_reason,
                    truncated_from=len(current.nodes),
                ),
                truncated_from=len(current.nodes),
            )
        return ExecuteResult(node=current.nodes[0], trace=trace)

    def execute_all(
        self,
        tree: IElementTree,
        root: TreeNode,
        locator: Locator,
    ) -> ExecuteAllResult:
        """
        Выполнить pipeline и вернуть все узлы финального ElementSet.

        Используйте при исследовании UI (Jupyter, подбор индекса), когда
        последний шаг даёт множество (FindDescendants/Filter без Take).
        Для сценариев и driver.resolve — execute().
        """
        current, trace = self._run_pipeline(tree, root, locator)
        return ExecuteAllResult(nodes=current.nodes, trace=trace)

    def _run_pipeline(
        self,
        tree: IElementTree,
        root: TreeNode,
        locator: Locator,
    ) -> tuple[ElementSet[TreeNode], LocatorTrace]:
        current = ElementSet.single(root)
        steps: list[TraceStep] = []

        for step_index, op in enumerate(locator.ops):
            in_count = len(current)
            current, status = self._apply_op(tree, current, op)
            out_count = len(current)
            steps.append(
                TraceStep(
                    step_index=step_index,
                    op=op,
                    in_count=in_count,
                    out_count=out_count,
                    status=status,
                )
            )
            if status != "ok":
                trace = LocatorTrace(
                    steps=tuple(steps),
                    failed_step_index=step_index,
                    failure_reason=_failure_reason(status),
                )
                raise LocatorNotFoundError(
                    f"Locator failed at step {step_index}: {_format_op_short(op)}",
                    trace=trace,
                )

        if current.is_empty():
            trace = LocatorTrace(steps=tuple(steps))
            raise LocatorNotFoundError("Locator pipeline produced empty result", trace=trace)

        return current, LocatorTrace(steps=tuple(steps))

    def _apply_op(
        self,
        tree: IElementTree,
        current: ElementSet[TreeNode],
        op: LocatorOp,
    ) -> tuple[ElementSet[TreeNode], TraceStatus]:
        if isinstance(op, ChildOp):
            return self._child(tree, current, op.index)
        if isinstance(op, FindDescendantsOp):
            return self._find_descendants(tree, current, op)
        if isinstance(op, FilterOp):
            return self._filter(tree, current, op.where)
        if isinstance(op, TakeOp):
            return self._take(current, op.index)
        raise LocatorNotFoundError(
            f"Unknown op: {op!r}",
            trace=LocatorTrace(steps=()),
        )

    def _child(
        self,
        tree: IElementTree,
        current: ElementSet[TreeNode],
        index: int,
    ) -> tuple[ElementSet[TreeNode], TraceStatus]:
        out: list[TreeNode] = []
        for node in current.nodes:
            children = tree.children(node)
            if index < len(children):
                out.append(children[index])
        if not out:
            return ElementSet.empty(), "empty"
        return ElementSet.from_list(out), "ok"

    def _find_descendants(
        self,
        tree: IElementTree,
        current: ElementSet[TreeNode],
        op: FindDescendantsOp,
    ) -> tuple[ElementSet[TreeNode], TraceStatus]:
        out: list[TreeNode] = []
        for node in current.nodes:
            if op.limit is None:
                out.extend(tree.descendants(node, where=op.where, depth=op.depth))
            else:
                out.extend(
                    self._walk_descendants(tree, node, op.where, op.depth, op.limit)
                )
            if op.limit is not None and len(out) >= op.limit:
                out = out[: op.limit]
                break
        if not out:
            return ElementSet.empty(), "empty"
        return ElementSet.from_list(out), "ok"

    def _walk_descendants(
        self,
        tree: IElementTree,
        root: TreeNode,
        where: FilterWhere,
        depth: int | None,
        limit: int | None,
    ) -> list[TreeNode]:
        """BFS: узлы на расстоянии 1..depth от root, фильтр where, ранняя остановка по limit."""
        out: list[TreeNode] = []
        frontier: list[TreeNode] = list(tree.children(root))
        level = 1
        while frontier:
            if depth is not None and level > depth:
                break
            next_frontier: list[TreeNode] = []
            for node in frontier:
                if _matches_where(tree.properties(node), where):
                    out.append(node)
                    if limit is not None and len(out) >= limit:
                        return out
                next_frontier.extend(tree.children(node))
            frontier = next_frontier
            level += 1
        return out

    def _filter(
        self,
        tree: IElementTree,
        current: ElementSet[TreeNode],
        where: FilterWhere,
    ) -> tuple[ElementSet[TreeNode], TraceStatus]:
        filtered = current.filter_nodes(
            lambda n: _matches_where(tree.properties(n), where)
        )
        if filtered.is_empty():
            return filtered, "empty"
        return filtered, "ok"

    def _take(
        self,
        current: ElementSet[TreeNode],
        index: int,
    ) -> tuple[ElementSet[TreeNode], TraceStatus]:
        if index >= len(current):
            return ElementSet.empty(), "index_out_of_range"
        return ElementSet.single(current.nodes[index]), "ok"


def _matches_where(props: ElementProperties, where: FilterWhere) -> bool:
    for key, expected in where.items():
        actual = getattr(props, key, None)
        if actual != expected:
            return False
    return True


def _failure_reason(status: TraceStatus) -> str:
    if status == "empty":
        return "empty_set"
    if status == "index_out_of_range":
        return "take_index_out_of_range"
    return status


def _format_op_short(op: LocatorOp) -> str:
    from autoui.locators.trace import _format_op

    return _format_op(op)
