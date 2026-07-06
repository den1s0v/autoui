"""Tests for PywinautoElementTree where mapping and wrapping."""

from __future__ import annotations

from dataclasses import dataclass, field

from autoui.drivers.pywinauto_tree import _split_where, _wrap_children


@dataclass
class FakeBackend:
    def generic_wrapper_class(self, info: object) -> object:
        return Wrapped(info)


@dataclass
class Wrapped:
    info: object

    def draw_outline(self, **kwargs: object) -> None:
        pass

    @property
    def element_info(self) -> object:
        return self.info

    def is_enabled(self) -> bool:
        return True

    def is_visible(self) -> bool:
        return True


@dataclass
class FakeParent:
    backend: FakeBackend = field(default_factory=FakeBackend)


def test_split_where_maps_name_to_title() -> None:
    native, post = _split_where({"control_type": "Button", "name": "OK", "automation_id": "x"})
    assert native == {"control_type": "Button", "title": "OK", "automation_id": "x"}
    assert post == {}


def test_split_where_operators_go_to_post() -> None:
    native, post = _split_where(
        {"class_name": {"$contains": "logo"}, "name": "OK"}
    )
    assert native == {"title": "OK"}
    assert post == {"class_name": {"$contains": "logo"}}


def test_wrap_children_wraps_element_info() -> None:
    parent = FakeParent()
    raw = [object(), object()]
    wrapped = _wrap_children(parent, raw)
    assert len(wrapped) == 2
    assert all(isinstance(w, Wrapped) for w in wrapped)


def test_wrap_children_keeps_wrappers() -> None:
    parent = FakeParent()
    already = [Wrapped(object())]
    assert _wrap_children(parent, already) is already
