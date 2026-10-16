import pytest

from errors import (
    Batch,
    Number,
    Object,
    String,
    StructError,
    assert_,
    check_line,
    noted,
)

SAMPLE = Object({"id": String(), "radius": Number()})
LINES = [
    '{"id": "S1", "radius": 17.99}\n',
    '{"id": "S2", "radius": "x"}\n',
    '{"id": "S3", "radius": 13.54\n',
    '{"id": "S4", "radius": 11.42}\n',
]


@pytest.mark.id("tst_q1y9j7")
def test_noted():
    """Adds a note to an error raised in its block"""
    with pytest.raises(StructError) as raised, noted("Export 2026-10-16"):
        assert_(42, String())
    assert raised.value.__notes__ == ["Export 2026-10-16"]
    with pytest.raises(ZeroDivisionError) as divided, noted("Export 2026-10-16"):
        print(1 / 0)
    assert divided.value.__notes__ == ["Export 2026-10-16"]


@pytest.mark.id("tst_uu9ds4")
def test_noted_after():
    """Adds its note after the notes an error already has"""
    with pytest.raises(StructError) as raised, noted("Export 2026-10-16"):
        check_line(LINES[1], 2, SAMPLE)
    assert raised.value.__notes__ == ["Line 2", "Export 2026-10-16"]
    with noted("Export 2026-10-16"):
        record = check_line(LINES[0], 1, SAMPLE)
    assert record == {"id": "S1", "radius": 17.99}


@pytest.mark.id("tst_l05z3l")
def test_batch():
    """Keeps each line's record, and gives itself to the block"""
    with Batch(SAMPLE) as batch:
        assert isinstance(batch, Batch)
        batch.check(LINES[0], 1)
        batch.check(LINES[3], 4)
    assert batch.records == [
        {"id": "S1", "radius": 17.99},
        {"id": "S4", "radius": 11.42},
    ]
    assert batch.errors == []


@pytest.mark.id("tst_gjj3un")
def test_batch_group():
    """Raises the lines' errors together when the block ends"""
    with pytest.raises(ExceptionGroup) as raised, Batch(SAMPLE) as batch:
        for number, line in enumerate(LINES, 1):
            batch.check(line, number)
        assert len(batch.errors) == 2
    group = raised.value
    assert group.message == "2 of 4 lines failed"
    assert [str(error) for error in group.exceptions] == [
        "At path: radius -- Expected a number, but received: 'x'",
        "Line 3 isn't JSON",
    ]
    assert group.exceptions[0].__notes__ == ["Line 2"]
    assert len(batch.records) == 2


@pytest.mark.id("tst_4gimbe")
def test_batch_other_error():
    """Lets an error of the block's own go on, as it was"""
    with pytest.raises(KeyError), Batch(SAMPLE) as batch:
        batch.check(LINES[1], 2)
        print({}["radius"])
    assert len(batch.errors) == 1
