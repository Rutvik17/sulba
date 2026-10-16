import pytest

from form import build, enums

SPEC = [("radius", 5, 30), ("smoothness", 0.05, 0.17), ("texture", 9, 40)]


@pytest.mark.id("tst_28aox7")
def test_own_ranges():
    """Gives each field its own range"""
    checks = build(SPEC)
    assert checks["radius"](35) is not None
    assert checks["radius"](6) is None
    assert checks["texture"](35) is None
    assert checks["smoothness"](0.1) is None


@pytest.mark.id("tst_sqv8su")
def test_names():
    """Keeps each check's name"""
    for check in build(SPEC).values():
        assert check.__name__ == "number"


@pytest.mark.id("tst_4nack5")
def test_options_kept():
    """Keeps the options it was made with"""
    sides = ["left", "right"]
    side = enums(sides)
    sides.append("both")
    assert side("both") == "Expected one of `'left','right'`, but received: 'both'"


@pytest.mark.id("tst_ysrifp")
def test_wrong_kind():
    """Fails a value that isn't a number, without raising an error"""
    checks = build(SPEC)
    assert checks["radius"]("17.99") == "Expected a number, but received: '17.99'"
    assert checks["texture"](None) == "Expected a number, but received: None"
