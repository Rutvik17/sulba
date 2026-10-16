import pytest

from refine import cached, literal

# The codes of the patients the clinic's registry knows.
KNOWN = {f"S{i:05d}" for i in range(0, 1000, 4)}


def registry():
    """The registry's check of a sample's code, and the list of codes it's asked for."""
    asked = []

    def registered(value):
        asked.append(value)
        if value in KNOWN:
            return None
        return f"No patient has the code {value!r}"

    return registered, asked


@pytest.mark.id("tst_vhb2jf")
def test_once_a_day():
    """Looks each code up once"""
    check, asked = registry()
    check = cached(1000)(check)
    codes = [f"S{(i * 7) % 250:05d}" for i in range(5000)]
    for code in codes:
        assert check(code) == (
            None if code in KNOWN else f"No patient has the code {code!r}"
        )
    assert sorted(asked) == sorted(set(codes))


@pytest.mark.id("tst_tg6qrm")
def test_booleans_apart():
    """Keeps True apart from 1 and 1.0"""
    check = cached(8)(literal(1))
    assert check(1.0) is None
    assert check(True) == "Expected the literal `1`, but received: True"
    assert check(1) is None
    assert check(False) == "Expected the literal `1`, but received: False"


@pytest.mark.id("tst_ph9hgt")
def test_forgets_oldest():
    """Forgets the code used longest ago, and holds no more than its size"""
    check, asked = registry()
    check = cached(2)(check)
    for code in ["S00000", "S00004", "S00000", "S00008", "S00004", "S00000"]:
        check(code)
    assert asked == ["S00000", "S00004", "S00008", "S00004", "S00000"]
