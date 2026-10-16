from collections import Counter

import pytest

from service import Enums, Failure, Number, Object, String


@pytest.mark.id("tst_7bkztm")
def test_own_options():
    """Keeps each enums' options to itself"""
    side = Enums(["left", "right"])
    unit = Enums(["mm", "cm"])
    assert "mm" not in side
    assert "left" not in unit
    assert side.validate("mm").message == (
        "Expected one of `'left','right'`, but received: 'mm'"
    )


@pytest.mark.id("tst_j9ensj")
def test_enums_message():
    """Fails an enums' value with the clinic's message"""
    side = Enums(["left", "right"], message="Choose the left or the right side.")
    assert side.validate("top").message == "Choose the left or the right side."


@pytest.mark.id("tst_4bz81m")
def test_counted():
    """Gives failures the daily report can count"""
    sample = Object({"id": String(), "radius": Number()})
    records = [
        {"id": "S1", "radius": "x"},
        {"id": "S2", "radius": "x"},
        {"id": 3, "radius": 11.42},
    ]
    counts = Counter(
        failure for record in records for failure in sample.failures(record)
    )
    radius = Failure(("radius",), "number", "Expected a number, but received: 'x'")
    assert counts[radius] == 2
    assert len(counts) == 2


@pytest.mark.id("tst_pxte9s")
def test_union_kept():
    """Leaves a union as it was when it's joined into a wider one"""
    string, number = String(), Number()
    either = string | number
    wider = either | Object({})
    assert either.members == [string, number]
    assert {} not in either
    assert {} in wider
