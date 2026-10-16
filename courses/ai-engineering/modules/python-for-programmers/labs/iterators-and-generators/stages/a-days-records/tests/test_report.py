import io
import json

import pytest

from walk import number, report, string

SAMPLE = {"id": string, "radius": number, "tags": [string]}


def line(record):
    return json.dumps(record) + "\n"


@pytest.mark.id("tst_nj0vot")
def test_report():
    """Reports a day's failures by line"""
    lines = [
        line({"id": "S1", "radius": 17.99, "tags": []}),
        line({"id": "S2", "radius": "13.5", "tags": ["repeat", 4]}),
        line({"id": "S3", "radius": 11.2, "tags": [], "age": 51}),
    ]
    assert report(lines, SAMPLE, 10) == [
        (2, ("radius",), "Expected a number, but received: '13.5'"),
        (2, ("tags", 1), "Expected a string, but received: 4"),
        (3, ("age",), "Expected a value of type `never`, but received: `51`"),
    ]


@pytest.mark.id("tst_37esqm")
def test_limit():
    """Gives no more failures than the limit"""
    lines = [line({"id": i, "radius": 2.5, "tags": []}) for i in range(20)]
    found = report(lines, SAMPLE, 5)
    assert [line_no for line_no, _, _ in found] == [1, 2, 3, 4, 5]
    assert report(lines, SAMPLE, 0) == []


@pytest.mark.id("tst_fpgxcr")
def test_file():
    """Reads the lines of a file"""
    text = "".join(line({"id": "S1", "radius": 2.5, "tags": []}) for _ in range(9))
    text += line({"id": "S10", "radius": None, "tags": []})
    assert report(io.StringIO(text), SAMPLE, 10) == [
        (10, ("radius",), "Expected a number, but received: None")
    ]


@pytest.mark.id("tst_17js35")
def test_not_an_object():
    """Reports a line that holds no object"""
    lines = [line([1, 2]), line("S2"), line({"id": "S3", "radius": 1.5, "tags": []})]
    assert report(lines, SAMPLE, 10) == [
        (1, (), "Expected an object, but received: [1, 2]"),
        (2, (), "Expected an object, but received: 'S2'"),
    ]


@pytest.mark.id("tst_5etx1u")
def test_windows_lines():
    """Reads lines that end in \\r\\n"""
    lines = [json.dumps({"id": "S1", "radius": "x", "tags": []}) + "\r\n"]
    assert report(lines, SAMPLE, 10) == [
        (1, ("radius",), "Expected a number, but received: 'x'")
    ]
