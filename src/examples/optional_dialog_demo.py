"""
Пример optional dialog: probe + branch + postcondition_recovery.

    python -m autoui dry-run examples.optional_dialog_demo:export_scenario
"""

from __future__ import annotations

from autoui.actions.builtin import ClickAction, ReadTextAction, SequenceAction
from autoui.dsl.builder import branch, probe, scenario, step, uimap, window_exists
from autoui.dsl.precondition import skip_if_not_met, wait_until
from autoui.runtime.recovery import PostconditionRecovery
from autoui.uimap.element_ref import ElementRef

_map = uimap(
    {
        "export_btn": ElementRef(title="Экспорт"),
        "error_ok": ElementRef(title="OK"),
        "error_body": ElementRef(control_type="Text"),
    }
)

export_scenario = scenario(
    name="optional_dialog_export",
    entry="probe_error",
    uimap=_map,
    order=["probe_error", "handle_export_error", "verify_file"],
    steps={
        "probe_error": probe(
            "probe_error",
            when=[window_exists("Ошибка")],
            precondition_policy=wait_until(timeout=5, on_timeout="goto", goto_step="verify_file"),
            on_met="handle_export_error",
        ),
        "handle_export_error": step(
            "handle_export_error",
            action=SequenceAction(
                [
                    ReadTextAction("error_body", into="last_error"),
                    ClickAction("error_ok"),
                ]
            ),
            on_success="verify_file",
        ),
        "verify_file": step(
            "verify_file",
        ),
        "post_export": branch(
            "post_export",
            when=[window_exists("Ошибка экспорта")],
            then_steps=[
                step(
                    "extract",
                    action=ReadTextAction("error_body", into="last_error"),
                ),
            ],
            else_goto="verify_file",
        ),
        "dismiss_license": step(
            "dismiss_license",
            when=[window_exists("Лицензия")],
            precondition_policy=skip_if_not_met(),
            action=ClickAction("error_ok"),
        ),
    },
)
