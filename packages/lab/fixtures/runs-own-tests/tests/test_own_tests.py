import sys

import pytest

pytest_plugins = ["pytester"]


@pytest.fixture
def outcomes(pytester, pytestconfig):
    """How many of the tests in test_timer.py pass and fail, run inside this test."""
    root = pytestconfig.rootpath

    def run(*options):
        for name in ["timer", "test_timer"]:
            sys.modules.pop(name, None)
        pytester.makepyfile(
            timer=(root / "timer.py").read_text(), test_timer=(root / "test_timer.py").read_text()
        )
        passed, _, failed = pytester.inline_run(
            "-p", "no:terminal", "-p", "no:cacheprovider", *options
        ).countoutcomes()
        return passed, failed

    return run


@pytest.mark.id("tst_owns01")
def test_with_the_fixtures(outcomes):
    """The session's own tests get the loop, with the runner's fixtures"""
    assert outcomes("-p", "sulba_fixtures") == (2, 0)


@pytest.mark.id("tst_owns02")
def test_without_the_fixtures(outcomes):
    """Without them, they can't ask for it"""
    assert outcomes() == (0, 2)
