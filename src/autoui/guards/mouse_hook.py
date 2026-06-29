"""
Low-level mouse hook (WH_MOUSE_LL) для детекции активности пользователя.

Игнорирует события пока ctx.automation_active — см. README CoexistenceGuard.
"""

from __future__ import annotations

import ctypes
import threading
from ctypes import wintypes
from typing import Callable

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

WH_MOUSE_LL = 14
WM_MOUSEMOVE = 0x0200
WM_LBUTTONDOWN = 0x0201
WM_RBUTTONDOWN = 0x0204
WM_MBUTTONDOWN = 0x0207

LowLevelMouseProc = ctypes.CFUNCTYPE(ctypes.c_long, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)


class MouseHook:
    """Фоновый hook; callback при пользовательской активности мыши."""

    def __init__(self, on_activity: Callable[[], None], is_automation_active: Callable[[], bool]) -> None:
        self._on_activity = on_activity
        self._is_automation_active = is_automation_active
        self._hook_id = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._proc = LowLevelMouseProc(self._handler)

    def _handler(self, n_code: int, w_param: wintypes.WPARAM, l_param: wintypes.LPARAM) -> int:
        if n_code >= 0 and w_param in (WM_MOUSEMOVE, WM_LBUTTONDOWN, WM_RBUTTONDOWN, WM_MBUTTONDOWN):
            if not self._is_automation_active():
                self._on_activity()
        return user32.CallNextHookEx(self._hook_id, n_code, w_param, l_param)

    def _run_loop(self) -> None:
        class MSG(ctypes.Structure):
            _fields_ = [("hwnd", wintypes.HWND), ("message", wintypes.UINT), ("wParam", wintypes.WPARAM),
                        ("lParam", wintypes.LPARAM), ("time", wintypes.DWORD), ("pt", wintypes.POINT)]

        msg = MSG()
        self._hook_id = user32.SetWindowsHookExW(WH_MOUSE_LL, self._proc, kernel32.GetModuleHandleW(None), 0)
        while not self._stop.is_set():
            if user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        if self._hook_id:
            user32.UnhookWindowsHookEx(self._hook_id)

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)
