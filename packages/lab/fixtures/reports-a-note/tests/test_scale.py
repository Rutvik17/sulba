import pytest
from scale import double


@pytest.mark.id("tst_note01")
def test_doubles_many(record_property):
    """Doubles a thousand values"""
    values = list(range(1000))
    record_property("note", f"{len(values):,} values")
    assert double(values) == [2 * value for value in values]


@pytest.mark.id("tst_note02")
def test_keeps_its_note_on_failing(record_property):
    """Triples a value"""
    record_property("note", "1 value")
    assert double([1]) == [3]
