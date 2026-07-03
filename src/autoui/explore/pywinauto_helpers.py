"""
Хелперы pywinauto для интерактивного исследования UI.

Используются в Jupyter playground (autoui.explore); ядро runtime не импортирует.
"""

from __future__ import annotations

from typing import Any


def find_desktop_windows(target_window_title: str) -> list[Any]:
    """
    Окна рабочего стола, в заголовке которых есть подстрока target_window_title.

    UIA backend; порядок — как возвращает pywinauto Desktop.
    """
    from pywinauto import Desktop

    desktop = Desktop(backend="uia")
    results: list[Any] = []
    for window in desktop.windows():
        try:
            window_title = window.window_text() or ""
        except Exception:
            continue
        if target_window_title in window_title:
            results.append(window)
    return results


def filter_windows_by_title(windows: list[Any], target_window_title: str) -> list[Any]:
    """Фильтр уже полученного списка окон по подстроке заголовка."""
    results: list[Any] = []
    for window in windows:
        try:
            window_title = window.window_text() or ""
        except Exception:
            continue
        if target_window_title in window_title:
            results.append(window)
    return results


def path_from_root(element: Any) -> str:
    """Цепочка class_name | title от элемента до корня."""
    path: list[str] = []
    cur: Any | None = element
    while cur is not None:
        try:
            title = cur.window_text() or "<no title>"
            class_name = cur.class_name() or "<no class>"
        except Exception:
            title = "<no title>"
            class_name = "<no class>"
        path.append(f"{class_name} | {title}")
        try:
            cur = cur.parent()
        except Exception:
            break
    return " -> ".join(reversed(path))


def list_menu_items(menu_item: Any, indent: str = "") -> None:
    """Рекурсивный вывод пунктов меню (text | item_id)."""
    try:
        items = menu_item.items()
    except Exception:
        return
    for item in items:
        try:
            text = item.text()
            item_id = item.item_id()
        except Exception:
            text = "<?>"
            item_id = "<?>"
        print(f"{indent}{text} | {item_id}")
        try:
            sub = item.sub_menu()
        except Exception:
            sub = None
        if sub is not None:
            list_menu_items(sub, indent + "  ")
