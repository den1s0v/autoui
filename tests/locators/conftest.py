"""In-memory mock UI tree for locator unit tests."""

from __future__ import annotations

from dataclasses import dataclass, field

from autoui.abstractions.element_tree import ElementProperties, IElementTree


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
        ElementProperties(name="Экспорт", control_type="Button", enabled=True, visible=True)
    )
    cancel_btn = MockNode(
        ElementProperties(name="Отмена", control_type="Button", enabled=True, visible=True)
    )
    middle_custom = MockNode(
        ElementProperties(control_type="Custom"),
        children=[export_btn, cancel_btn],
    )
    left_custom = MockNode(ElementProperties(control_type="Custom"))
    ok_btn = MockNode(
        ElementProperties(
            name="OK",
            automation_id="btnOk",
            control_type="Button",
            enabled=True,
            visible=True,
        )
    )
    right_pane = MockNode(ElementProperties(control_type="Pane"), children=[ok_btn])
    pane0 = MockNode(ElementProperties(control_type="Pane"), children=[left_custom])
    pane1 = MockNode(ElementProperties(control_type="Pane"), children=[middle_custom])
    pane2 = MockNode(ElementProperties(control_type="Pane"), children=[right_pane])
    window = MockNode(
        ElementProperties(name="App", control_type="Window"),
        children=[pane0, pane1, pane2],
    )
    return window


class MockElementTree(IElementTree):
    def children(self, node: MockNode) -> list[MockNode]:
        return list(node.children)

    def descendants(self, node: MockNode) -> list[MockNode]:
        out: list[MockNode] = []

        def walk(n: MockNode) -> None:
            for child in n.children:
                out.append(child)
                walk(child)

        walk(node)
        return out

    def properties(self, node: MockNode) -> ElementProperties:
        return node.props
