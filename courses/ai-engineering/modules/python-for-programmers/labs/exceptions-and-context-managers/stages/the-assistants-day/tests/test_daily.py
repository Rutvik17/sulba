import pytest

from daily import (
    Batch,
    Number,
    Object,
    String,
    StructError,
    assert_,
    check_day,
    parse_line,
    report,
)

SAMPLE = Object({"id": String(), "radius": Number()})
GOOD = ['{"id": "S1", "radius": 17.99}\n', '{"id": "S4", "radius": 11.42}\n']


@pytest.mark.id("tst_epoafj")
def test_assert():
    """Raises a StructError for a record that fails"""
    with pytest.raises(StructError) as raised:
        assert_({"id": "S2", "radius": "x"}, SAMPLE)
    assert (
        str(raised.value) == "At path: radius -- Expected a number, but received: 'x'"
    )


@pytest.mark.id("tst_0r6f6o")
def test_parse_line():
    """Reads a line, and names a line that isn't JSON"""
    assert parse_line(GOOD[0], 1) == {"id": "S1", "radius": 17.99}
    with pytest.raises(ValueError, match="Line 3 isn't JSON"):
        parse_line('{"id": "S3", "radius": 13.54\n', 3)


@pytest.mark.id("tst_ktez1r")
def test_check_day():
    """Raises each failed line's error, noted with its line"""
    assert check_day(GOOD, SAMPLE) == [
        {"id": "S1", "radius": 17.99},
        {"id": "S4", "radius": 11.42},
    ]
    with pytest.raises(ExceptionGroup) as raised:
        check_day([GOOD[0], '{"id": 2, "radius": 1}\n'], SAMPLE)
    assert raised.value.message == "1 of 2 lines failed"
    assert raised.value.exceptions[0].__notes__ == ["Line 2"]


@pytest.mark.id("tst_ojv9jo")
def test_batch():
    """Keeps the records a batch checks"""
    with Batch(SAMPLE) as batch:
        for number, line in enumerate(GOOD, 1):
            batch.check(line, number)
    assert batch.records == [
        {"id": "S1", "radius": 17.99},
        {"id": "S4", "radius": 11.42},
    ]
    assert batch.errors == []


@pytest.mark.id("tst_p78bpt")
def test_report():
    """Logs nothing for a day without failures"""
    log = []
    report(GOOD, SAMPLE, log)
    assert log == []
