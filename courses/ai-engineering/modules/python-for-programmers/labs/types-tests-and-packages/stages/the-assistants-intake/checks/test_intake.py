from pathlib import Path

import pytest

from intake import IntakeError, note_of, take


@pytest.mark.id("tst_5luil1")
def test_missing_radius(typecheck):
    """Lets mypy catch a report line for a record without a radius"""
    Path("report_probe.py").write_text(
        'from intake import label\n\nlabel({"id": "S00001"})\n', encoding="utf-8"
    )
    assert typecheck("report_probe.py") == [
        'report_probe.py:3: error: Missing key "radius" for TypedDict "Sample"'
        "  [typeddict-item]"
    ]


@pytest.mark.id("tst_m58wy6")
def test_note_text():
    """Turns away a note that isn't text"""
    with pytest.raises(IntakeError) as raised:
        take({"id": "S00001", "radius": 17.99, "note": 7})
    assert str(raised.value) == "note"


@pytest.mark.id("tst_rsoly1")
def test_no_note():
    """Gives an empty note for a sample without one"""
    assert note_of(take({"id": "S00001", "radius": 17.99})) == ""


@pytest.mark.id("tst_z3e7ad")
def test_whole_radius():
    """Takes a radius that's a whole number"""
    assert take({"id": "S00001", "radius": 18}) == {"id": "S00001", "radius": 18}
    with pytest.raises(IntakeError):
        take({"id": "S00001", "radius": True})
