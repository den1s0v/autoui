"""Unit tests for where matching operators."""

from __future__ import annotations

import pytest

from autoui.locators.errors import LocatorFilterError
from autoui.locators.matching import match_condition, match_where, validate_where


def test_scalar_exact_match() -> None:
    assert match_where({"name": "OK"}, {"name": "OK"})
    assert not match_where({"name": "OK"}, {"name": "Cancel"})


def test_explicit_eq() -> None:
    assert match_where({"control_type": "Button"}, {"control_type": {"$eq": "Button"}})


def test_contains_on_string() -> None:
    props = {"class_name": "foo glass-in-app-menubar__logo-btn bar"}
    assert match_where(props, {"class_name": {"$contains": "logo-btn"}})
    assert not match_where(props, {"class_name": {"$contains": "missing"}})


def test_contains_on_texts_list() -> None:
    props = {"texts": ["", "Cursor"]}
    assert match_where(props, {"texts": {"$contains": "Cursor"}})
    assert not match_where(props, {"texts": {"$contains": "VSCode"}})


def test_word_on_class_name() -> None:
    props = {"class_name": "prefix glass-in-app-menubar__logo-btn suffix"}
    assert match_where(props, {"class_name": {"$word": "glass-in-app-menubar__logo-btn"}})
    assert not match_where(props, {"class_name": {"$word": "logo-btn"}})


def test_missing_key_returns_false() -> None:
    assert not match_where({"name": "X"}, {"rich_text": "X"})


def test_none_value_matches() -> None:
    assert match_where({"control_id": None}, {"control_id": None})
    assert not match_where({"control_id": None}, {"control_id": 1})


def test_incompatible_type_for_word_returns_false() -> None:
    assert not match_condition(True, {"$word": "x"})


def test_validate_where_rejects_unknown_operator() -> None:
    with pytest.raises(LocatorFilterError, match="unknown operator"):
        validate_where({"name": {"$regex": ".*"}})


def test_validate_where_rejects_multi_op_dict() -> None:
    with pytest.raises(LocatorFilterError, match="exactly one key"):
        validate_where({"name": {"$eq": "a", "$contains": "b"}})


def test_validate_where_accepts_operators() -> None:
    validate_where(
        {
            "name": "Cursor",
            "class_name": {"$contains": "logo"},
            "rich_text": {"$contains": "Cur"},
        }
    )
