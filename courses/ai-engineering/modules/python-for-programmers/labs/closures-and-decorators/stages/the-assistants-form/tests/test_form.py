import pytest

from form import build, enums

SPEC = [("radius", 5, 30), ("smoothness", 0.05, 0.17), ("texture", 9, 40)]


@pytest.mark.id("tst_394u50")
def test_fields():
    """Builds a check for each field"""
    assert list(build(SPEC)) == ["radius", "smoothness", "texture"]


@pytest.mark.id("tst_3g0m9w")
def test_in_range():
    """Passes measurements in range"""
    checks = build(SPEC)
    assert checks["radius"](17.99) is None
    assert checks["texture"](10.38) is None


@pytest.mark.id("tst_1eeu60")
def test_out_of_range():
    """Fails measurements out of range"""
    checks = build(SPEC)
    for field in ["radius", "texture"]:
        assert checks[field](45) == (
            "Expected a value of type `number` with refinement `range`, "
            "but received: `45`"
        )


@pytest.mark.id("tst_sonj4f")
def test_counts():
    """Counts each field's failures"""
    radius = build(SPEC)["radius"]
    radius(45)
    radius(17.99)
    assert radius.failed == 1


@pytest.mark.id("tst_gkox2r")
def test_enums():
    """Passes the options and fails the rest"""
    side = enums(["left", "right"])
    assert side("left") is None
    assert side("top") == "Expected one of `'left','right'`, but received: 'top'"
