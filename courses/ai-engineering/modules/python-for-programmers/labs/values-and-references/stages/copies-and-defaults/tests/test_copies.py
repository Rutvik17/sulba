import copy

import pytest

from values import known_fields, unknown_fields, with_defaults


@pytest.mark.id("tst_pkdf6p")
def test_superstruct():
    """Passes superstruct's test for an object's defaults"""
    # Its fixture in test/validation/defaulted/mixin.ts.
    found = with_defaults({"version": 0}, {"title": "Untitled"})
    assert found == {"version": 0, "title": "Untitled"}
    assert list(found) == ["version", "title"]


@pytest.mark.id("tst_18pdt5")
def test_keeps_values():
    """Keeps the values a record has, falsy ones too"""
    record = {"count": 0, "note": "", "urgent": False, "tags": []}
    defaults = {"count": 1, "note": "none", "urgent": True, "tags": lambda: ["new"]}
    assert with_defaults(record, defaults) == record


@pytest.mark.id("tst_7yo753")
def test_null():
    """Keeps a null as a value"""
    assert with_defaults({"title": None}, {"title": "Untitled"}) == {"title": None}


@pytest.mark.id("tst_8vmev2")
def test_leaves_record():
    """Leaves the record as it was"""
    record = {"id": "842302", "tags": ["urgent"]}
    before = copy.deepcopy(record)
    for defaults in [{"note": ""}, {}]:
        assert with_defaults(record, defaults) is not record
        assert record == before
    assert known_fields(record, ["id", "tags"]) is not record
    assert record == before


@pytest.mark.id("tst_xdz9xk")
def test_factories():
    """Makes each default afresh from its factory"""
    defaults = {"tags": list}
    first = with_defaults({}, defaults)
    second = with_defaults({}, defaults)
    first["tags"].append("urgent")
    assert second["tags"] == []
    assert defaults == {"tags": list}


@pytest.mark.id("tst_8gu4ky")
def test_known_fields():
    """Keeps the fields it knows, in the record's order"""
    record = {"texture": 10.38, "unknown": True, "radius": 17.99}
    found = known_fields(record, ["radius", "texture"])
    assert found == {"texture": 10.38, "radius": 17.99}
    assert list(found) == ["texture", "radius"]


@pytest.mark.id("tst_prfr0v")
def test_unknown_fields():
    """Lists the unknown fields in the record's order"""
    names = list("qwertyuiopasdfghjklzxcvbnm")
    record = dict.fromkeys(["id", *names], 1)
    assert unknown_fields(record, {"id": "string"}) == names
    assert unknown_fields({"id": 1}, ["id"]) == []
