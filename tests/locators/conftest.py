"""In-memory mock UI tree for locator unit tests."""

from __future__ import annotations

from dataclasses import dataclass, field

from autoui.abstractions.element_tree import ElementProperties, IElementTree
from autoui.locators.matching import match_where


@dataclass
class MockNode:
    """Узел mock-дерева."""

    props: ElementProperties
    children: list[MockNode] = field(default_factory=list)


def build_sample_tree() -> MockNode:
    """
    Window
      Pane (x3)
        [0] Custom
        [1] Custom
          Button name=Экспорт
          Button name=Отмена
        [2] Pane
          Button name=OK automation_id=btnOk
    """
    export_btn = MockNode(
        {
            "name": "Экспорт",
            "control_type": "Button",
            "enabled": True,
            "visible": True,
        }
    )
    cancel_btn = MockNode(
        {
            "name": "Отмена",
            "control_type": "Button",
            "enabled": True,
            "visible": True,
        }
    )
    middle_custom = MockNode({"control_type": "Custom"}, children=[export_btn, cancel_btn])
    left_custom = MockNode({"control_type": "Custom"})
    ok_btn = MockNode(
        {
            "name": "OK",
            "automation_id": "btnOk",
            "control_type": "Button",
            "enabled": True,
            "visible": True,
        }
    )
    right_pane = MockNode({"control_type": "Pane"}, children=[ok_btn])
    pane0 = MockNode({"control_type": "Pane"}, children=[left_custom])
    pane1 = MockNode({"control_type": "Pane"}, children=[middle_custom])
    pane2 = MockNode({"control_type": "Pane"}, children=[right_pane])
    window = MockNode({"name": "App", "control_type": "Window"}, children=[pane0, pane1, pane2])
    return window


class MockElementTree(IElementTree):
    def children(self, node: MockNode) -> list[MockNode]:
        return list(node.children)

    def descendants(
        self,
        node: MockNode,
        *,
        where: dict | None = None,
        depth: int | None = None,
    ) -> list[MockNode]:
        out: list[MockNode] = []
        frontier: list[MockNode] = list(node.children)
        level = 1
        while frontier:
            if depth is not None and level > depth:
                break
            next_frontier: list[MockNode] = []
            for child in frontier:
                out.append(child)
                next_frontier.extend(child.children)
            frontier = next_frontier
            level += 1
        if not where:
            return out
        return [n for n in out if match_where(n.props, where)]

    def properties(self, node: MockNode) -> ElementProperties:
        return dict(node.props)
