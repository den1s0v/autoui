"""
autoui.explore — playground для подбора локаторов (Jupyter / интерактив).

Зависит от pywinauto через drivers. Runtime сценариев не использует этот модуль.
"""

from autoui.explore.highlight import HighlightManager
from autoui.explore.playground import ExplorerSession
from autoui.explore.pywinauto_helpers import (
    filter_windows_by_title,
    find_desktop_windows,
    list_menu_items,
    path_from_root,
)

__all__ = [
    "ExplorerSession",
    "HighlightManager",
    "filter_windows_by_title",
    "find_desktop_windows",
    "list_menu_items",
    "path_from_root",
]
