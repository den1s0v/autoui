"""LocatorTrace — диагностика шагов pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from autoui.locators.ops import LocatorOp

TraceStatus = Literal["ok", "empty", "index_out_of_range"]


@dataclass(frozen=True)
class TraceStep:
    step_index: int
    op: LocatorOp
    in_count: int
    out_count: int
    status: TraceStatus


@dataclass(frozen=True)
class LocatorTrace:
    steps: tuple[TraceStep, ...]
    failed_step_index: int | None = None
    failure_reason: str | None = None

    def format_diagnostic(self) -> str:
        if not self.steps:
            return "Locator pipeline: (empty)"

        total = len(self.steps)
        if self.failed_step_index is None:
            lines = [f"Locator pipeline ({total} ops), success:"]
        else:
            lines = [
                f"Locator pipeline ({total} ops), failed at step {self.failed_step_index}:"
            ]

        for step in self.steps:
            marker = ""
            if step.step_index == self.failed_step_index:
                marker = "  ← FAILED"
            lines.append(
                f"  [{step.step_index}] {_format_op(step.op)}"
                f"  in={step.in_count}  out={step.out_count}  {step.status}{marker}"
            )
        if self.failure_reason:
            lines.append(f"  reason: {self.failure_reason}")
        return "\n".join(lines)


def _format_op(op: LocatorOp) -> str:
    from autoui.locators.ops import ChildOp, FilterOp, FindDescendantsOp, TakeOp

    if isinstance(op, ChildOp):
        return f"child(index={op.index})"
    if isinstance(op, FindDescendantsOp):
        return f"find_descendants({op.where})"
    if isinstance(op, FilterOp):
        return f"filter({op.where})"
    if isinstance(op, TakeOp):
        return f"take(index={op.index})"
    return repr(op)
