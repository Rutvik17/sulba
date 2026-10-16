import pytest

from structs import Sample

RECORD = {"id": "S1", "radius": 17.99, "texture": 10.38, "smoothness": 0.1184}


@pytest.mark.id("tst_h7sx8w")
def test_parse():
    """Makes a sample of a record's fields"""
    sample = Sample.parse(RECORD)
    assert sample == Sample("S1", 17.99, 10.38, 0.1184)
    assert sample.radius == 17.99


@pytest.mark.id("tst_0lawhp")
def test_wrong_kind():
    """Raises a TypeError with the first failure, explained"""
    with pytest.raises(TypeError) as raised:
        Sample.parse({**RECORD, "radius": "x"})
    assert (
        str(raised.value) == "At path: radius -- Expected a number, but received: 'x'"
    )


@pytest.mark.id("tst_sshsv6")
def test_unknown_and_missing():
    """Fails a record with a field the struct doesn't know, or without one it does"""
    with pytest.raises(TypeError) as raised:
        Sample.parse({**RECORD, "note": "repeat"})
    assert str(raised.value) == (
        "At path: note -- Expected a value of type `never`, but received: `'repeat'`"
    )
    without = {key: value for key, value in RECORD.items() if key != "texture"}
    with pytest.raises(TypeError) as raised:
        Sample.parse(without)
    assert str(raised.value) == (
        "At path: texture -- Expected a number, but received: undefined"
    )


@pytest.mark.id("tst_y4pcz2")
def test_not_a_record():
    """Fails a value that isn't an object"""
    with pytest.raises(TypeError) as raised:
        Sample.parse("S1")
    assert str(raised.value) == "Expected an object, but received: 'S1'"


@pytest.mark.id("tst_lebadn")
def test_repr():
    """Shows a sample with its fields"""
    assert repr(Sample.parse(RECORD)) == (
        "Sample(id='S1', radius=17.99, texture=10.38, smoothness=0.1184)"
    )
