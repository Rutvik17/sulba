import pytest
from booking import problems


@pytest.mark.id("tst_jsc001")
def test_valid():
    """Finds nothing wrong with a valid booking"""
    assert problems({"name": "Ana", "repair": "brakes", "bikes": 2}) == []


@pytest.mark.id("tst_jsc002")
def test_invalid():
    """Says what is wrong with an invalid booking, and where"""
    assert problems({"name": "", "repair": "paint", "bikes": 4, "note": "soon"}) == [
        "/: Additional properties are not allowed ('note' was unexpected)",
        "/bikes: 4 is greater than the maximum of 3",
        "/name: '' should be non-empty",
        "/repair: 'paint' is not one of ['tune-up', 'brakes', 'puncture']",
    ]
