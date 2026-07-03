"""Unit tests for HighlightManager."""

from __future__ import annotations

from dataclasses import dataclass, field

from autoui.explore.highlight import DEFAULT_CLEAR_COLOUR, HighlightManager


@dataclass
class MockControl:
    calls: list[tuple[str, dict]] = field(default_factory=list)

    def draw_outline(self, **kwargs: object) -> None:
        self.calls.append(("draw_outline", dict(kwargs)))


def test_highlight_draws_green() -> None:
    ctrl = MockControl()
    mgr = HighlightManager()
    mgr.highlight(ctrl, colour="green", thickness=4)
    assert len(ctrl.calls) == 1
    assert ctrl.calls[0] == ("draw_outline", {"thickness": 4, "colour": "green"})


def test_second_highlight_clears_first() -> None:
    first = MockControl()
    second = MockControl()
    mgr = HighlightManager()
    mgr.highlight(first, colour="green")
    mgr.highlight(second, colour="red")
    assert len(first.calls) == 2
    assert first.calls[1] == (
        "draw_outline",
        {"thickness": 4, "colour": DEFAULT_CLEAR_COLOUR},
    )
    assert second.calls[0] == ("draw_outline", {"thickness": 4, "colour": "red"})


def test_clear_without_prior_highlight() -> None:
    mgr = HighlightManager()
    mgr.clear()  # no-op
