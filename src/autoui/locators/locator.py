"""Locator — immutable pipeline операций поиска."""

from __future__ import annotations

from dataclasses import dataclass

from autoui.locators.ops import (
    ChildOp,
    FilterOp,
    FilterWhere,
    FindDescendantsOp,
    LocatorOp,
    TakeOp,
)


@dataclass(frozen=True)
class Locator:
    """Программа поиска элемента — последовательность ops."""

    ops: tuple[LocatorOp, ...]

    def __init__(self, ops: list[LocatorOp] | tuple[LocatorOp, ...]) -> None:
        object.__setattr__(self, "ops", tuple(ops))

    @classmethod
    def find(cls, **where: object) -> Locator:
        """
        Shorthand: FindDescendants(where) → Take(0).

        Ключи: name, automation_id, class_name, control_type, enabled, visible.
        """
        clean: FilterWhere = {k: v for k, v in where.items() if v is not None}
        if not clean:
            raise ValueError("Locator.find() requires at least one filter field")
        return cls((FindDescendantsOp(where=clean), TakeOp(index=0)))
