import json

import pytest

from intake import enums, literal, with_defaults


@pytest.mark.id("tst_3wtsbv")
def test_literal_from_json():
    """Takes the form's values for the literal they equal"""
    sent = json.loads('{"version": 1000, "method": "aspiration"}')
    assert literal(sent["version"], 1000) is None
    assert literal(sent["method"], "aspiration") is None


@pytest.mark.id("tst_hgm82d")
def test_enums_booleans():
    """Takes no boolean for a number"""
    assert enums(1, [0, 1]) is None
    assert enums(True, [0, 1]) == "Expected one of `0,1`, but received: True"
    assert enums(False, [0, 1]) == "Expected one of `0,1`, but received: False"


@pytest.mark.id("tst_mo44jh")
def test_falsy_values():
    """Keeps the values a record has, falsy ones too"""
    record = {"count": 0, "note": "", "urgent": False}
    found = with_defaults(record, {"count": 1, "note": "none", "urgent": True})
    assert found == {"count": 0, "note": "", "urgent": False}


@pytest.mark.id("tst_o5h3oh")
def test_record_unchanged():
    """Leaves the record as it was"""
    record = {"id": "842302"}
    with_defaults(record, {"note": "none", "tags": list})
    assert record == {"id": "842302"}
