import pytest

from walker import failures, first_failures, number, problems, string

SAMPLE = {"id": string, "radius": number, "tags": [string]}


@pytest.mark.id("tst_voz1qt")
def test_passes():
    """Passes a record that matches"""
    assert (
        list(failures({"id": "S1", "radius": 17.99, "tags": ["repeat"]}, SAMPLE)) == []
    )


@pytest.mark.id("tst_ewqrui")
def test_field():
    """Finds a field that fails"""
    found = list(failures({"id": "S1", "radius": "17.99", "tags": []}, SAMPLE))
    assert found == [(("radius",), "Expected a number, but received: '17.99'")]


@pytest.mark.id("tst_eydte5")
def test_missing_and_unknown():
    """Finds missing and unknown fields"""
    found = list(failures({"id": "S1", "tags": [], "age": 51}, SAMPLE))
    assert found == [
        (("radius",), "Missing"),
        (("age",), "Expected a value of type `never`, but received: `51`"),
    ]


@pytest.mark.id("tst_z99vyl")
def test_problems():
    """Explains a record's failures"""
    found = problems({"id": 1, "radius": "x", "tags": []}, SAMPLE)
    assert "At path: radius -- Expected a number, but received: 'x'" in found
    assert problems({"id": "S1", "radius": 2.5, "tags": []}, SAMPLE) == []


@pytest.mark.id("tst_0qeykg")
def test_first_failures():
    """Takes the first failures of a day's records"""
    records = [
        {"id": "S1", "radius": i if i % 5 else "x", "tags": []} for i in range(30)
    ]
    assert [index for index, _, _ in first_failures(records, SAMPLE, 2)] == [0, 5]
