"""
Пример сценария для Double Commander.

Запуск (при открытом Double Commander):
    python -m autoui dry-run examples.double_commander_demo:demo_scenario
"""

from __future__ import annotations

from autoui.dsl.builder import (
    scenario,
    step,
    uimap,
    wait,
    window_exists,
)
from autoui.dsl.precondition import skip_if_not_met
from autoui.uimap.element_ref import ElementRef

# Карта элементов — при смене UI правится только этот блок.
_map = uimap(
    {
        "toolbar": ElementRef(class_name="ToolbarWindow32"),
    }
)

demo_scenario = scenario(
    name="double_commander_demo",
    entry="wait_app",
    uimap=_map,
    order=["wait_app", "dismiss_license", "done"],
    app_selector="Double Commander",
    primary_window_title="Double Commander",
    steps={
        "wait_app": step(
            "wait_app",
            when=[window_exists("Double Commander")],
            action=wait(0.5),
            on_success="dismiss_license",
        ),
        "dismiss_license": step(
            "dismiss_license",
            when=[window_exists("Лицензия")],
            precondition_policy=skip_if_not_met(),
            # action закрытия — добавить ключ в uimap когда известен automation_id
            on_success="done",
        ),
        "done": step(
            "done",
            action=wait(0.1),
        ),
    },
)
