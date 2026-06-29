"""
Python DSL — фабрики scenario, step, actions, conditions.

Синтаксический сахар над dataclass runtime.
"""

from __future__ import annotations

from typing import Sequence

from autoui.actions.builtin import (
    AppendVarToFileAction,
    ClickAction,
    ReadTextAction,
    SequenceAction,
    SetTextAction,
    WaitAction,
)
from autoui.conditions.builtin import ControlExists, FileExists, WindowExists
from autoui.runtime.precondition import PreconditionPolicy
from autoui.runtime.recovery import PostconditionRecovery
from autoui.runtime.retry import RetryPolicy
from autoui.runtime.scenario import Scenario
from autoui.runtime.step import ActionStep, BranchStep, ProbeStep
from autoui.uimap.map import UIMap


def uimap(elements: dict) -> UIMap:
    return UIMap(elements)


def click(target: str) -> ClickAction:
    return ClickAction(target)


def set_text(target: str, text: str | None = None, var: str | None = None) -> SetTextAction:
    return SetTextAction(target=target, text=text, var=var)


def read_text(target: str, into: str) -> ReadTextAction:
    return ReadTextAction(target=target, into=into)


def wait(seconds: float) -> WaitAction:
    return WaitAction(timeout=seconds)


def sequence(*actions) -> SequenceAction:
    return SequenceAction(actions=actions)


def append_ctx_to_file(path: str, var: str) -> AppendVarToFileAction:
    return AppendVarToFileAction(path=path, var=var)


def expect_window(title: str) -> WindowExists:
    return WindowExists(title)


def window_exists(title: str) -> WindowExists:
    return WindowExists(title)


def control_exists(target: str) -> ControlExists:
    return ControlExists(target)


def file_exists(path: str | None = None, var: str | None = None) -> FileExists:
    return FileExists(path=path, var=var)


def step(
    name: str,
    *,
    action=None,
    when: Sequence | None = None,
    expect: Sequence | None = None,
    precondition_policy: PreconditionPolicy | None = None,
    retry: RetryPolicy | None = None,
    postcondition_recovery: PostconditionRecovery | None = None,
    on_success: str | None = None,
) -> ActionStep:
    return ActionStep(
        name=name,
        action=action,
        when=list(when or []),
        expect=list(expect or []),
        precondition_policy=precondition_policy or PreconditionPolicy(),
        retry=retry or RetryPolicy(),
        postcondition_recovery=postcondition_recovery,
        on_success=on_success,
    )


def probe(
    name: str,
    *,
    when: Sequence,
    precondition_policy: PreconditionPolicy | None = None,
    on_met: str | None = None,
    on_success: str | None = None,
) -> ProbeStep:
    return ProbeStep(
        name=name,
        when=list(when),
        precondition_policy=precondition_policy or PreconditionPolicy(mode="wait"),
        on_met=on_met,
        on_success=on_success,
    )


def branch(
    name: str,
    *,
    when: Sequence,
    then_steps: Sequence,
    else_goto: str | None = None,
) -> BranchStep:
    return BranchStep(
        name=name,
        when=list(when),
        then_steps=list(then_steps),
        else_goto=else_goto,
    )


def scenario(
    name: str,
    entry: str,
    steps: dict,
    uimap: UIMap,
    order: list[str] | None = None,
    watchers: list | None = None,
    app_selector: str | int | None = None,
    primary_window_title: str | None = None,
    **kwargs,
) -> Scenario:
    return Scenario(
        name=name,
        entry=entry,
        steps=steps,
        uimap=uimap,
        order=order,
        watchers=list(watchers or []),
        app_selector=app_selector,
        primary_window_title=primary_window_title,
        **kwargs,
    )


def watcher(name: str, when, action, priority: int = 0):
    from autoui.watchers.manager import Watcher

    when_list = [when] if not isinstance(when, list) else when
    return Watcher(name=name, when=when_list, action=action, priority=priority)
