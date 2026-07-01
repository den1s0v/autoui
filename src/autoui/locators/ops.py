"""Операции pipeline-локатора."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

FilterWhere = dict[str, Any]

FILTER_KEYS = frozenset(
    {
        "name",
        "automation_id",
        "class_name",
        "control_type",
        "enabled",
        "visible",
    }
)


def validate_filter_where(where: FilterWhere) -> FilterWhere:
    unknown = set(where) - FILTER_KEYS
    if unknown:
        raise ValueError(f"Unknown filter keys: {sorted(unknown)}")
    return where


@dataclass(frozen=True)
class ChildOp:
    index: int

    @property
    def op(self) -> str:
        return "child"


@dataclass(frozen=True)
class FindDescendantsOp:
    where: FilterWhere

    def __post_init__(self) -> None:
        validate_filter_where(self.where)

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
