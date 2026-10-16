"""Tests of the port's structs."""

import math

import pytest

from typed import StructError, array, create, nullable, number, string


@pytest.mark.parametrize("value", [17.99, 3, 0, -2.5])
def test_number_passes(value):
    assert create(value, number()) == value


@pytest.mark.parametrize("value", [True, False, math.nan, "17.99", None])
def test_number_fails(value):
    with pytest.raises(StructError):
        create(value, number())


@pytest.mark.parametrize("value", [[], [17.99], [17.99, 3]])
def test_array_passes(value):
    assert create(value, array(number())) == value


@pytest.mark.parametrize("value", [[17.99, "3"], ["3", 17.99], (17.99, 3), "17.99"])
def test_array_fails(value):
    with pytest.raises(StructError):
        create(value, array(number()))


@pytest.mark.parametrize("value", [None, "repeat"])
def test_nullable_passes(value):
    assert create(value, nullable(string())) == value


def test_nullable_fails():
    with pytest.raises(StructError):
        create(7, nullable(string()))


def test_message():
    with pytest.raises(StructError) as raised:
        create(["S00001", 7], array(string()))
    assert str(raised.value) == (
        "Expected a value of type `array`, but received: `['S00001', 7]`"
    )
    assert isinstance(raised.value, TypeError)
