import dataclasses
import tracemalloc

import pytest

from structs import Sample

RECORD = {"id": "S1", "radius": 17.99, "texture": 10.38, "smoothness": 0.1184}
# The samples the memory check holds, and the most of the memory of objects without
# __slots__ that they may take.
SAMPLES = 20_000
SHARE = 0.75


class Unslotted:
    """A sample's fields, in an object of a class without __slots__."""

    def __init__(self, id, radius, texture, smoothness):
        self.id = id
        self.radius = radius
        self.texture = texture
        self.smoothness = smoothness


def held(make, rows):
    """The memory taken by the objects make gives for rows, and the objects."""
    tracemalloc.start()
    try:
        before, _ = tracemalloc.get_traced_memory()
        made = [make(*row) for row in rows]
        after, _ = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return after - before, made


@pytest.mark.id("tst_ew9yer")
def test_memory(record_property):
    """Holds many samples in little memory"""
    rows = [
        (f"S{i:05d}", 6.25 + i % 23, 9.71 + i % 29, 0.05 + i % 11 / 100)
        for i in range(SAMPLES)
    ]
    taken, samples = held(Sample, rows)
    plain, _ = held(Unslotted, rows)
    record_property("note", f"{taken / plain:.0%} of the memory")
    assert len(samples) == SAMPLES
    assert taken <= SHARE * plain


@pytest.mark.id("tst_betds9")
def test_frozen():
    """Can't be changed, and goes in a set once"""
    sample = Sample.parse(RECORD)
    with pytest.raises(dataclasses.FrozenInstanceError):
        sample.radius = 20.57
    assert sample.radius == 17.99
    other = Sample.parse({**RECORD, "id": "S2"})
    assert len({sample, Sample.parse(dict(RECORD)), other}) == 2


@pytest.mark.id("tst_r59fod")
def test_subclass():
    """Parses to the class it's called on"""

    class Followup(Sample):
        """A sample taken at a later visit."""

        def label(self):
            return f"Follow-up of {self.id}"

    followup = Followup.parse(RECORD)
    assert type(followup) is Followup
    assert followup.label() == "Follow-up of S1"
