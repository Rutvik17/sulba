import copy

import pytest

from values import boolean, enums, number, prepare, string


def tags(value):
    if isinstance(value, list) and all(isinstance(tag, str) for tag in value):
        return None
    return f"Expected a list of strings, but received: {value!r}"


def side(value):
    return enums(value, ["left", "right"])


FORM = {
    "id": string,
    "side": side,
    "radius": number,
    "texture": number,
    "urgent": boolean,
    "tags": tags,
    "note": string,
}


def records(count):
    """count records as the form sends them: most pass, some fail and some leave fields
    out or add their own."""
    made = []
    for i in range(count):
        record = {
            "id": f"S{i:06d}",
            "side": "left" if i % 2 else "right",
            "radius": 6.25 + i % 23,
            "texture": 10 + i % 29,
        }
        if i % 3 == 0:
            record["tags"] = ["repeat"]
        elif i % 3 == 1:
            record["tags"] = []
        if i % 5 == 0:
            record["urgent"] = True
        if i % 7 == 0:
            del record["texture"]
        if i % 11 == 0:
            record["extra"] = {"source": ["paper form"]}
        made.append(record)
    return made


def containers(value):
    """Every list and dict in value, value among them."""
    found = []
    waiting = [value]
    while waiting:
        item = waiting.pop()
        if isinstance(item, (list, dict)):
            found.append(item)
            waiting.extend(item.values() if isinstance(item, dict) else item)
    return found


@pytest.mark.id("tst_gae6i4")
def test_records_unchanged():
    """Leaves the form's records as they were"""
    sent = records(500)
    before = copy.deepcopy(sent)
    defaults = {"urgent": False, "tags": list, "note": ""}
    for record in sent:
        prepare(record, FORM, defaults)
    assert sent == before
    assert defaults == {"urgent": False, "tags": list, "note": ""}


@pytest.mark.id("tst_n6cct9")
def test_nothing_shared():
    """Shares no list or dict"""
    sent = records(500)
    defaults = {"urgent": False, "tags": ["new"], "note": ""}
    prepared = [prepare(record, FORM, defaults)[0] for record in sent]
    held = {id(item): "the defaults" for item in containers(defaults)}
    for record in sent:
        held.update(
            (id(item), "the record it came from") for item in containers(record)
        )
    for found in prepared:
        for item in containers(found):
            assert id(item) not in held, (
                f"A prepared record shares {item!r} with {held[id(item)]}."
            )
            held[id(item)] = "another prepared record"


@pytest.mark.id("tst_hdndfa")
def test_unknown_order():
    """Reports unknown fields in the record's order"""
    names = list("qwertyuiopasdfghjklzxcvbnm")
    sample = {
        "id": "S000001",
        "side": "left",
        "radius": 7.25,
        "texture": 11,
        "tags": [],
    }
    record = {**sample, **dict.fromkeys(names, 1)}
    _, failures = prepare(record, FORM, {"urgent": False, "tags": list, "note": ""})
    assert failures == [(name, "Unknown field") for name in names]
