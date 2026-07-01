"""ElementSet — единая коллекция узлов в pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class ElementSet(Generic[T]):
    nodes: tuple[T, ...]

    @classmethod
    def empty(cls) -> ElementSet[T]:
        return cls(())

    @classmethod
    def single(cls, node: T) -> ElementSet[T]:
        return cls((node,))

    @classmethod
    def from_list(cls, nodes: list[T]) -> ElementSet[T]:
        return cls(tuple(nodes))

    def __len__(self) -> int:
        return len(self.nodes)

    def is_empty(self) -> bool:
        return len(self.nodes) == 0

    def map_nodes(self, fn: Callable[[T], T]) -> ElementSet[T]:
        return ElementSet(tuple(fn(n) for n in self.nodes))

    def flat_map(self, fn: Callable[[T], ElementSet[T]]) -> ElementSet[T]:
        out: list[T] = []
        for node in self.nodes:
            out.extend(fn(node).nodes)
        return ElementSet(tuple(out))

    def filter_nodes(self, predicate: Callable[[T], bool]) -> ElementSet[T]:
        return ElementSet(tuple(n for n in self.nodes if predicate(n)))
