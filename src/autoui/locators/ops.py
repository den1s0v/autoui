"""Операции pipeline-локатора."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from autoui.locators.matching import validate_filter_where

FilterWhere = dict[str, Any]


@dataclass(frozen=True)
class ChildOp:
    index: int

    @property
    def op(self) -> str:
        return "child"


@dataclass(frozen=True)
class FindDescendantsOp:
    where: FilterWhere
    depth: int | None = None
    limit: int | None = None

    def __post_init__(self) -> None:
        validate_filter_where(self.where)
        if self.depth is not None and self.depth < 1:
            raise ValueError("depth must be >= 1 or None")
        if self.limit is not None and self.limit < 1:
            raise ValueError("limit must be >= 1 or None")

    @property
    def op(self) -> str:
        return "find_descendants"


@dataclass(frozen=True)
class FilterOp:
    where: FilterWhere

    def __post_init__(self) -> None:
        validate_filter_where(self.where)

    @property
    def op(self) -> str:
        return "filter"


@dataclass(frozen=True)
class TakeOp:
    index: int

    @property
    def op(self) -> str:
        return "take"


LocatorOp = ChildOp | FindDescendantsOp | FilterOp | TakeOp
