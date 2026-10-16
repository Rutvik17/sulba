import pytest

from intake import IntakeError, label, note_of, take


@pytest.mark.id("tst_m3ztro")
def test_take():
    """Takes a record"""
    record = {"id": "S00001", "radius": 17.99, "note": "repeat"}
    assert take(record) == record


@pytest.mark.id("tst_grkn99")
def test_turns_away():
    """Turns away a record without an id"""
    with pytest.raises(IntakeError):
        take({"radius": 17.99})


@pytest.mark.id("tst_gdbcwm")
def test_report():
    """Labels a sample and gives its note"""
    sample = take({"id": "S00002", "radius": 20.57, "note": "repeat"})
    assert label(sample) == "S00002 (20.57)"
    assert note_of(sample) == "repeat"


@pytest.mark.id("tst_6wnudq")
def test_strict(typecheck):
    """Passes mypy --strict"""
    assert typecheck("intake.py") == []
