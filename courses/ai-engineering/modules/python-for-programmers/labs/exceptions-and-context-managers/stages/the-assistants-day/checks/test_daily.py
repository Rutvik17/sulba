import json

import pytest

from daily import Batch, Number, Object, String, StructError, parse_line, report

SAMPLE = Object({"id": String(), "radius": Number()})
DAY = [
    '{"id": "S1", "radius": 17.99}\n',
    '{"id": "S2", "radius": "x"}\n',
    '{"id": "S3", "radius": 13.54\n',
    '{"id": "S4", "radius": 11.42}\n',
]


@pytest.mark.id("tst_hhdhys")
def test_batch_goes_on():
    """Keeps a failed line's error in its batch, and goes on to the next line"""
    with pytest.raises(ExceptionGroup) as raised, Batch(SAMPLE) as batch:
        for number, line in enumerate(DAY, 1):
            batch.check(line, number)
    assert [type(error) for error in raised.value.exceptions] == [
        StructError,
        ValueError,
    ]
    assert len(batch.records) == 2


@pytest.mark.id("tst_t5wi4p")
def test_block_error():
    """Lets an error of the block's own go on, as it was"""
    with pytest.raises(KeyError), Batch(SAMPLE) as batch:
        batch.check(DAY[0], 1)
        print({}["radius"])


@pytest.mark.id("tst_omj1nm")
def test_cause():
    """Keeps json's error as the cause of a line that isn't JSON"""
    with pytest.raises(ValueError) as raised:
        parse_line(DAY[2], 3)
    assert isinstance(raised.value.__cause__, json.JSONDecodeError)


@pytest.mark.id("tst_e80rvh")
def test_report():
    """Logs each failed record, and lets every other error go on"""
    log = []
    with pytest.raises(ExceptionGroup) as raised:
        report(DAY, SAMPLE, log)
    assert log == ["Line 2: At path: radius -- Expected a number, but received: 'x'"]
    assert [str(error) for error in raised.value.exceptions] == ["Line 3 isn't JSON"]
