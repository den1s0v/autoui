"""
Notepad++ — открыть диалог поиска и выполнить «Найти далее».

Заготовка: логика сценария готова, в UIMap ниже нужно подставить рабочие локаторы
(Inspect.exe / Accessibility Insights / pywinauto print_control_identifiers).

Запуск (Notepad++ должен быть открыт):
    python -m autoui dry-run examples.notepadpp_find_demo:notepadpp_find_scenario
    python -m autoui run examples.notepadpp_find_demo:notepadpp_find_scenario

Поисковый запрос по умолчанию — константа DEFAULT_SEARCH_QUERY ниже.
Для своего текста: --vars search_query=ваш_текст
(шаг fill_and_find_next читает ctx[\"search_query\"]).
"""

from __future__ import annotations

from autoui.actions.builtin import ClickAction, SequenceAction, SetTextAction, WaitAction
from autoui.dsl.builder import (
    control_exists,
    probe,
    scenario,
    step,
    uimap,
    wait,
    window_exists,
)
from autoui.dsl.precondition import skip_if_not_met, wait_until
from autoui.locators import FindDescendantsOp, Locator, TakeOp

# --- Настройки сценария ---

NOTEPAD_WINDOW_TITLE = "Notepad++"
"""Подстрока заголовка главного окна."""

DEFAULT_SEARCH_QUERY = "hello"

# ---------------------------------------------------------------------------
# UIMap — подобрать локаторы (единственный блок для правок после инспекции UI)
# ---------------------------------------------------------------------------
#
# find_dialog / search_edit — диалог «Найти» / «Find»:
#   • поле «Найти что» — Edit; control_exists удобно вешать на search_edit.
#
# menu_search → menu_find — «Поиск» → «Найти...» (RU) или Search → Find... (EN).
#
# find_next_btn — «Найти далее» / «Find Next».
#
# Альтернатива меню в open_find_via_menu:
#   заменить SequenceAction на PressHotkeyAction(keys=[\"^\", \"f\"]).
#
# Pipeline-пример:
#   Locator([ChildOp(0), FindDescendantsOp(where={\"control_type\": \"Edit\"}), TakeOp(0)])
# ---------------------------------------------------------------------------

_map = uimap(
    {
        # TODO: признак открытого диалога поиска
        "find_dialog": Locator.find(
            name="Find",
            control_type="Window",
        ),
        # TODO: поле «Найти что» / «Find what»
        "search_edit": Locator.find(
            control_type="Edit",
        ),
        # TODO: «Найти далее» / «Find Next»
        "find_next_btn": Locator.find(
            name="Find Next",
            control_type="Button",
        ),
        # TODO: меню «Search» / «Поиск»
        "menu_search": Locator(
            [
                FindDescendantsOp(where={"control_type": "MenuBar"}),
                TakeOp(0),
                FindDescendantsOp(where={"name": "Search"}),
                TakeOp(0),
            ]
        ),
        # TODO: «Find...» / «Найти...»
        "menu_find": Locator.find(
            name="Find...",
            control_type="MenuItem",
        ),
        # --- RU (раскомментировать и подправить шаги при русском UI) ---
        # "menu_search": Locator.find(name="Поиск", control_type="MenuItem"),
        # "menu_find": Locator.find(name="Найти...", control_type="MenuItem"),
        # "find_next_btn": Locator.find(name="Найти далее", control_type="Button"),
        # "find_dialog": Locator.find(name="Найти", control_type="Window"),
    }
)

notepadpp_find_scenario = scenario(
    name="notepadpp_find",
    entry="wait_notepad",
    uimap=_map,
    app_selector=NOTEPAD_WINDOW_TITLE,
    primary_window_title=NOTEPAD_WINDOW_TITLE,
    order=[
        "wait_notepad",
        "probe_find_dialog",
        "open_find_via_menu",
        "ensure_find_dialog",
        "fill_and_find_next",
        "done",
    ],
    steps={
        "wait_notepad": step(
            "wait_notepad",
            when=[window_exists(NOTEPAD_WINDOW_TITLE)],
            precondition_policy=wait_until(timeout=15, on_timeout="fail"),
            action=wait(0.3),
            on_success="probe_find_dialog",
        ),
        "probe_find_dialog": probe(
            "probe_find_dialog",
            when=[control_exists("find_dialog")],
            precondition_policy=skip_if_not_met(),
            on_met="fill_and_find_next",
            on_success="open_find_via_menu",
        ),
        "open_find_via_menu": step(
            "open_find_via_menu",
            action=SequenceAction(
                [
                    ClickAction("menu_search"),
                    WaitAction(0.3),
                    ClickAction("menu_find"),
                ]
            ),
            on_success="ensure_find_dialog",
        ),
        "ensure_find_dialog": step(
            "ensure_find_dialog",
            when=[control_exists("find_dialog")],
            precondition_policy=wait_until(timeout=5, on_timeout="fail"),
            action=wait(0.2),
            on_success="fill_and_find_next",
        ),
        "fill_and_find_next": step(
            "fill_and_find_next",
            when=[control_exists("search_edit")],
            precondition_policy=wait_until(timeout=5, on_timeout="fail"),
            action=SequenceAction(
                [
                    # text= для быстрого старта; для --vars search_query=... замените на var="search_query"
                    SetTextAction("search_edit", text=DEFAULT_SEARCH_QUERY),
                    ClickAction("find_next_btn"),
                ]
            ),
            on_success="done",
        ),
        "done": step(
            "done",
            action=wait(0.1),
        ),
    },
)
