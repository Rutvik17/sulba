import pytest

from walker import failures, first_failures, number, problems, string

SAMPLE = {"id": string, "radius": number, "tags": [string]}


@pytest.mark.id("tst_vsijp1")
def test_inside_arrays():
    """Finds failures inside arrays"""
    found = list(failures({"id": "S1", "radius": 2.5, "tags": ["repeat", 3]}, SAMPLE))
    assert found == [(("tags", 1), "Expected a string, but received: 3")]
    found = list(failures([{"id": "S1"}, {"id": 2}], [{"id": string}]))
    assert found == [((1, "id"), "Expected a string, but received: 2")]


@pytest.mark.id("tst_rh8wlr")
def test_not_an_object():
    """Rejects a value that isn't an object"""
    assert list(failures("S1", SAMPLE)) == [
        ((), "Expected an object, but received: 'S1'")
    ]
    schema = {"id": string, "address": {"street": string}}
    assert list(failures({"id": "S1", "address": "1 Main St"}, schema)) == [
        (("address",), "Expected an object, but received: '1 Main St'")
    ]


@pytest.mark.id("tst_sx24ba")
def test_every_problem():
    """Explains every failure, the first one too"""
    assert problems({"id": 1, "radius": 2.5, "tags": []}, SAMPLE) == [
        "At path: id -- Expected a string, but received: 1"
    ]
    assert problems({"id": 1, "radius": "x", "tags": []}, SAMPLE) == [
        "At path: id -- Expected a string, but received: 1",
        "At path: radius -- Expected a number, but received: 'x'",
    ]


@pytest.mark.id("tst_igb742")
def test_reads_no_further():
    """Reads no record past the failures it gives"""
    read = []

    def day():
        for i in range(10_000):
            record = {"id": f"S{i:05d}", "radius": "x" if i % 10 == 0 else 2.5}
            read.append(record)
            yield {**record, "tags": []}

    found = first_failures(day(), SAMPLE, 3)
    assert [index for index, _, _ in found] == [0, 10, 20]
    assert len(read) == 21
