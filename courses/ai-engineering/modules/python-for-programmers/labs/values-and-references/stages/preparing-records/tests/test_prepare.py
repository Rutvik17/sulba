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
DEFAULTS = {"urgent": False, "tags": list, "note": ""}
SAMPLE = {
    "id": "842302",
    "side": "left",
    "radius": 17.99,
    "texture": 10.38,
    "urgent": True,
    "tags": ["repeat"],
    "note": "Second sample",
}


def run(record):
    return prepare(record, FORM, DEFAULTS)


@pytest.mark.id("tst_9gnmjh")
def test_passes():
    """Prepares a record that passes"""
    found, failures = run(dict(reversed(SAMPLE.items())))
    assert failures == []
    assert found == SAMPLE
    assert list(found) == list(FORM)


@pytest.mark.id("tst_u5wanz")
def test_failures():
    """Reports each field that fails, in the form's order"""
    record = {**SAMPLE, "texture": "10.38", "side": True, "radius": float("nan")}
    found, failures = run(record)
    assert failures == [
        ("side", "Expected one of `'left','right'`, but received: True"),
        ("radius", "Expected a number, but received: nan"),
        ("texture", "Expected a number, but received: '10.38'"),
    ]
    assert found["texture"] == "10.38"


@pytest.mark.id("tst_j6p3oh")
def test_defaults():
    """Fills in the fields a record leaves out"""
    record = {key: SAMPLE[key] for key in ["id", "side", "radius", "texture"]}
    found, failures = run(record)
    assert failures == []
    assert found == {**record, "urgent": False, "tags": [], "note": ""}


@pytest.mark.id("tst_97b4uc")
def test_missing():
    """Reports a field with no default as missing"""
    record = {key: value for key, value in SAMPLE.items() if key != "radius"}
    found, failures = run(record)
    assert failures == [("radius", "Missing")]
    assert "radius" not in found
    assert list(found) == [key for key in FORM if key != "radius"]


@pytest.mark.id("tst_ezi5ri")
def test_unknown():
    """Drops and reports the fields the form doesn't know, after its own"""
    record = {"zone": 3, **SAMPLE, "age": 51, "texture": None}
    found, failures = run(record)
    assert failures == [
        ("texture", "Expected a number, but received: None"),
        ("zone", "Unknown field"),
        ("age", "Unknown field"),
    ]
    assert list(found) == list(FORM)


@pytest.mark.id("tst_gqllzi")
def test_null():
    """Keeps a null for a field that has a default"""
    found, failures = run({**SAMPLE, "note": None})
    assert found["note"] is None
    assert failures == [("note", "Expected a string, but received: None")]
