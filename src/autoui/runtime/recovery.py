"""
PostconditionRecovery — восстановление после провала expect.

Не путать с PreconditionPolicy.on_timeout (фаза when).
См. README.md — PostconditionRecovery.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from autoui.core.enums import PostconditionOutcome

if TYPE_CHECKING:
    from autoui.abstractions.action import IAction


@dataclass
class PostconditionRecovery:
    """
    Вызывается когда expect не прошли после исчерпания RetryPolicy.

    action — например закрыть диалог ошибки.
    then — что делать дальше: повторить шаг, skip, goto, fail.
    """

    action: IAction | None = None
    then: PostconditionOutcome = "retry_step"
    goto_step: str | None = None
