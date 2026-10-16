import pytest

from walk import check_records, first_failure, first_failures, number, string

SAMPLE = {"id": string, "radius": number, "tags": [string]}


def counted(records, read):
    """The records, one at a time, each noted in read as it's taken."""
    for record in records:
        read.append(record)
        yield record


def day(count):
    """count records as a generator, every tenth with its radius as text."""
    return (
        {"id": f"S{i:05d}", "radius": str(i) if i % 10 == 0 else 10.5, "tags": []}
        for i in range(count)
    )


@pytest.mark.id("tst_oeh9im")
def test_first_failure():
    """Gives the first failure, or None"""
    record = {"id": 1, "radius": "x", "tags": []}
    assert first_failure(record, SAMPLE) == (
        ("id",),
        "Expected a string, but received: 1",
    )
    assert first_failure({"id": "S1", "radius": 4.5, "tags": []}, SAMPLE) is None


@pytest.mark.id("tst_ikodrj")
def test_first_failure_stops():
    """Checks nothing after the first failure"""
    checked = []

    def logged(value):
        checked.append(value)
        return number(value)

    first_failure({"a": "x", "b": 1, "c": 2}, {"a": logged, "b": logged, "c": logged})
    assert checked == ["x"]


@pytest.mark.id("tst_pbxain")
def test_check_records():
    """Gives each record's failures with its index"""
    records = [
        {"id": "S1", "radius": 4.5, "tags": []},
        {"id": 2, "radius": "x", "tags": [3]},
    ]
    assert list(check_records(records, SAMPLE)) == [
        (1, ("id",), "Expected a string, but received: 2"),
        (1, ("radius",), "Expected a number, but received: 'x'"),
        (1, ("tags", 0), "Expected a string, but received: 3"),
    ]


@pytest.mark.id("tst_bc7bhq")
def test_check_records_lazy():
    """Reads each record only when it's needed"""
    read = []
    walking = check_records(counted(day(1000), read), SAMPLE)
    assert read == []
    assert next(walking)[0] == 0
    assert len(read) == 1
    assert next(walking)[0] == 10
    assert len(read) == 11


@pytest.mark.id("tst_zdadvg")
def test_first_failures():
    """Gives the first failures, reading no record past them"""
    read = []
    found = first_failures(counted(day(100_000), read), SAMPLE, 3)
    assert [index for index, _, _ in found] == [0, 10, 20]
    assert found[0] == (0, ("radius",), "Expected a number, but received: '0'")
    assert len(read) == 21


@pytest.mark.id("tst_4vn5ks")
def test_fewer_failures():
    """Gives every failure when there are fewer than asked for"""
    found = first_failures(day(25), SAMPLE, 10)
    assert [index for index, _, _ in found] == [0, 10, 20]
    assert first_failures(day(25), SAMPLE, 0) == []
