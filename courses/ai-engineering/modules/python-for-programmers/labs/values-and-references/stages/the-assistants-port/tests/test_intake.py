import pytest

from intake import enums, known_fields, literal, number, with_defaults


@pytest.mark.id("tst_iifblf")
def test_numbers():
    """Takes numbers and rejects the rest"""
    assert number(17.99) is None
    assert number("17.99") == "Expected a number, but received: '17.99'"


@pytest.mark.id("tst_1996o6")
def test_literal():
    """Takes the literal and rejects others"""
    assert literal(42, 42) is None
    assert literal("B", "B") is None
    assert literal(41, 42) == "Expected the literal `42`, but received: 41"


@pytest.mark.id("tst_p2cqat")
def test_enums():
    """Takes the options and rejects others"""
    assert enums("right", ["left", "right"]) is None
    assert enums("top", ["left", "right"]) == (
        "Expected one of `'left','right'`, but received: 'top'"
    )


@pytest.mark.id("tst_ein9m2")
def test_defaults():
    """Fills in the fields a record leaves out"""
    found = with_defaults({"id": "842302"}, {"note": "", "tags": list})
    assert found == {"id": "842302", "note": "", "tags": []}


@pytest.mark.id("tst_zomnx6")
def test_known_fields():
    """Keeps only the fields it knows"""
    assert known_fields({"id": "842302", "extra": 1}, ["id"]) == {"id": "842302"}
