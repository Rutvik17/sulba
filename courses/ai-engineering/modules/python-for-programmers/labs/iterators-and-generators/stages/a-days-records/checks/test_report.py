import json
import tracemalloc

import pytest

from walk import number, report, string

SAMPLE = {"id": string, "radius": number, "tags": [string]}
# The day the memory check reports on, and the most it may hold at once.
LINES = 10_000
MEMORY = 1_000_000


def day(count, read=None):
    """count lines as a generator, every thousandth with its radius as text."""
    for i in range(count):
        if read is not None:
            read.append(i)
        radius = str(i) if i % 1000 == 0 else 6.25 + i % 23
        yield (
            json.dumps({"id": f"S{i:05d}", "radius": radius, "tags": ["repeat"]}) + "\n"
        )


@pytest.mark.id("tst_fewhov")
def test_reads_no_further():
    """Reads no line past the failures it gives"""
    read = []
    found = report(day(10_000, read), SAMPLE, 3)
    assert [line_no for line_no, _, _ in found] == [1, 1001, 2001]
    assert len(read) == 2001


@pytest.mark.id("tst_oupytg")
def test_memory(record_property):
    """Holds one record at a time"""
    tracemalloc.start()
    try:
        found = report(day(LINES), SAMPLE, 100)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    record_property("note", f"{peak / 1000:,.0f} kB at most")
    assert len(found) == 10
    assert peak < MEMORY
