import json

import pytest

from errors import (
    Number,
    Object,
    String,
    StructError,
    check_day,
    check_line,
    parse_line,
    report,
)

SAMPLE = Object({"id": String(), "radius": Number()})
DAY = [
    '{"id": "S1", "radius": 17.99}\n',
    '{"id": "S2", "radius": "x"}\n',
    '{"id": "S3", "radius": 13.54\n',
    '{"id": "S4", "radius": 11.42}\n',
    '{"id": "S5", "radius": 20.29, "note": "repeat"}\n',
]


@pytest.mark.id("tst_z48eei")
def test_parse_line():
    """Reads a line's record, and names a line that isn't JSON"""
    assert parse_line(DAY[0], 1) == {"id": "S1", "radius": 17.99}
    with pytest.raises(ValueError) as raised:
        parse_line(DAY[2], 3)
    assert str(raised.value) == "Line 3 isn't JSON"
    assert isinstance(raised.value.__cause__, json.JSONDecodeError)


@pytest.mark.id("tst_25vprk")
def test_check_line():
    """Notes the line of a record that fails"""
    assert check_line(DAY[0], 1, SAMPLE) == {"id": "S1", "radius": 17.99}
    with pytest.raises(StructError) as raised:
        check_line(DAY[1], 2, SAMPLE)
    assert (
        str(raised.value) == "At path: radius -- Expected a number, but received: 'x'"
    )
    assert raised.value.__notes__ == ["Line 2"]


@pytest.mark.id("tst_xh435r")
def test_check_day():
    """Raises every line's error together, in order"""
    assert check_day([DAY[0], DAY[3]], SAMPLE) == [
        {"id": "S1", "radius": 17.99},
        {"id": "S4", "radius": 11.42},
    ]
    with pytest.raises(ExceptionGroup) as raised:
        check_day(DAY, SAMPLE)
    group = raised.value
    assert group.message == "3 of 5 lines failed"
    assert [type(error) for error in group.exceptions] == [
        StructError,
        ValueError,
        StructError,
    ]
    assert [str(error) for error in group.exceptions] == [
        "At path: radius -- Expected a number, but received: 'x'",
        "Line 3 isn't JSON",
        "At path: note -- Expected a value of type `never`, but received: `'repeat'`",
    ]
    assert group.exceptions[2].__notes__ == ["Line 5"]


@pytest.mark.id("tst_42okd8")
def test_report():
    """Logs each line that fails its struct, and passes the rest on"""
    log = []
    report([DAY[0], DAY[1], DAY[3], DAY[4]], SAMPLE, log)
    assert log == [
        "Line 2: At path: radius -- Expected a number, but received: 'x'",
        "Line 4: At path: note -- Expected a value of type `never`, but received: `'repeat'`",
    ]
    log = []
    with pytest.raises(ExceptionGroup) as raised:
        report(DAY, SAMPLE, log)
    assert len(log) == 2
    assert [str(error) for error in raised.value.exceptions] == ["Line 3 isn't JSON"]
    assert raised.value.message == "3 of 5 lines failed"
