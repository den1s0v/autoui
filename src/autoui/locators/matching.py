"""
Сопоставление where с properties узла.

validate_where — при создании op (неверный синтаксис → LocatorFilterError).
match_where — при обходе дерева; отсутствие ключа у узла → False, без исключений.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from autoui.locators.errors import LocatorFilterError

MATCH_OPS = frozenset({"$eq", "$contains", "$word"})


def validate_where(where: dict[str, Any]) -> dict[str, Any]:
    """Проверить форму условий where; имена полей не ограничиваются."""
    for key, condition in where.items():
        if not isinstance(key, str):
            raise LocatorFilterError(f"where key must be str, got {type(key)!r}")
        _validate_condition(condition, field=key)
    return where


def validate_filter_where(where: dict[str, Any]) -> dict[str, Any]:
    """Обёртка для ops.__post_init__ (ValueError вместо LocatorFilterError)."""
    try:
        return validate_where(where)
    except LocatorFilterError as exc:
        raise ValueError(str(exc)) from exc


def _validate_condition(condition: Any, *, field: str) -> None:
    if _is_scalar_condition(condition):
        return
    if isinstance(condition, dict):
        if len(condition) != 1:
            raise LocatorFilterError(
                f"where[{field!r}]: operator dict must have exactly one key, "
                f"got {list(condition)}"
            )
        op = next(iter(condition))
        if op not in MATCH_OPS:
            raise LocatorFilterError(f"where[{field!r}]: unknown operator {op!r}")
        return
    raise LocatorFilterError(
        f"where[{field!r}]: invalid condition type {type(condition)!r}"
    )


def _is_scalar_condition(condition: Any) -> bool:
    return not isinstance(condition, dict)


def match_where(props: Mapping[str, Any], where: Mapping[str, Any]) -> bool:
    """
    Все условия where должны выполниться.

    Ключ отсутствует у узла → False (узел пропускается).
    """
    for key, condition in where.items():
        if key not in props:
            return False
        if not match_condition(props[key], condition):
            return False
    return True


def match_condition(actual: Any, expected: Any) -> bool:
    """Сравнение одного поля; несовместимый тип оператора → False."""
    if isinstance(expected, dict):
        if len(expected) != 1:
            return False  # Неверный формат условия сравнения (должен быть один оператор с $ в начале и значение для него).
        op, val = next(iter(expected.items()))
        if op == "$eq":
            # Сравнение на равенство.
            return actual == val
        if op == "$contains":
            # Сравнение на вхождение строки в строку или в любой элемент списка строк.
            if isinstance(actual, str):
                return val in actual
            if isinstance(actual, (list, tuple)):
                return any(isinstance(item, str) and val in item for item in actual)
            return False
        if op == "$word":
            # Сравнение на вхождение слова в строку (наподобие \b word \b в регулярных выражениях).
            if not isinstance(actual, str):
                return False
            return val in actual.split()
        return False
    return actual == expected


def is_exact_scalar_condition(condition: Any) -> bool:
    """Скалярное условие (точное равенство) — для native pywinauto acceleration."""
    return _is_scalar_condition(condition)
