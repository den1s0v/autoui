"""
HighlightManager — подсветка элементов draw_outline с авто-снятием предыдущей рамки.
"""

from __future__ import annotations

from typing import Any

DEFAULT_CLEAR_COLOUR = 0xDDDDDD


class HighlightManager:
    """
    Перед новой подсветкой снимает предыдущую слабой рамкой (0xDDDDDD).
    """

    def __init__(
        self,
        *,
        clear_colour: int | str = DEFAULT_CLEAR_COLOUR,
        default_thickness: int = 4,
    ) -> None:
        self._clear_colour = clear_colour
        self._default_thickness = default_thickness
        self._last: Any | None = None
        self._last_thickness: int = default_thickness

    def highlight(
        self,
        control: Any,
        *,
        colour: str | int = "green",
        thickness: int | None = None,
    ) -> None:
        if control is None:
            return
        self.clear()
        thick = thickness if thickness is not None else self._default_thickness
        try:
            control.draw_outline(thickness=thick, colour=colour)
            self._last = control
            self._last_thickness = thick
        except Exception:
            self._last = None

    def clear(self) -> None:
        if self._last is None:
            return
        try:
            self._last.draw_outline(
                thickness=self._last_thickness,
                colour=self._clear_colour,
            )
        except Exception:
            pass
        finally:
            self._last = None
