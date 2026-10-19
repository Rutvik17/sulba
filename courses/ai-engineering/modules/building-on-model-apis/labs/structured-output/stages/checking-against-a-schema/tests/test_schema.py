import json
from pathlib import Path

import pytest

from schema import Error, errors

RECORDED = json.loads(Path("references/validation.json").read_text(encoding="utf-8"))


def check(group):
    """Each case of the group gives jsonschema's errors: their paths and keywords."""
    for case in RECORDED["cases"][group]:
        found = errors(case["value"], case["schema"])
        assert all(isinstance(error, Error) and error.message for error in found)
        where = sorted([error.path, error.keyword] for error in found)
        assert where == case["errors"], (
            f"{json.dumps(case['value'], ensure_ascii=False)} against "
            f"{json.dumps(case['schema'], ensure_ascii=False)}"
        )


@pytest.mark.id("tst_s7e1j1")
def test_types():
    """Types: an integer is any number with no fractional part, and a bool is no number"""
    check("types")


@pytest.mark.id("tst_rqyh44")
def test_equality():
    """enum and const: equal values have the same type, and numbers are equal by value"""
    check("equality")


@pytest.mark.id("tst_4exil7")
def test_objects():
    """Objects: each property against its schema, required keys and extra keys"""
    check("objects")


@pytest.mark.id("tst_0j1ijr")
def test_arrays():
    """Arrays: each item against its schema, at its index in the path"""
    check("arrays")


@pytest.mark.id("tst_bg1x7g")
def test_strings():
    """Strings: lengths in characters, and a pattern found anywhere in the string"""
    check("strings")


@pytest.mark.id("tst_ul8zaw")
def test_numbers():
    """Numbers: a keyword applies only to values of its type"""
    check("numbers")


@pytest.mark.id("tst_gm87fk")
def test_formats():
    """format is a note on the schema, and checks nothing"""
    check("formats")


@pytest.mark.id("tst_b8pqdq")
def test_messages():
    """An error's message names the value, the key or the rule it fails"""
    booking = RECORDED["cases"]["objects"][3]
    found = {
        error.path: error.message
        for error in errors(booking["value"], booking["schema"])
    }
    assert "bmx" in found["$.bike"]
    assert "9:30" in found["$.time"]
    missing = RECORDED["cases"]["objects"][1]
    messages = [error.message for error in errors(missing["value"], missing["schema"])]
    assert any("phone" in message for message in messages)
    assert any("notes" in message for message in messages)
    extra = RECORDED["cases"]["objects"][2]
    [error] = errors(extra["value"], extra["schema"])
    assert "price" in error.message and "confirmed" in error.message
