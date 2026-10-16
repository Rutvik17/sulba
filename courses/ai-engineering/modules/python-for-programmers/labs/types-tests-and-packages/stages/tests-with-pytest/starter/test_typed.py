"""Tests of the port's structs."""

import math

import pytest

from typed import StructError, array, create, nullable, number, string


@pytest.mark.parametrize("value", [17.99, 3])
def test_number_passes(value):
    assert create(value, number()) == value
