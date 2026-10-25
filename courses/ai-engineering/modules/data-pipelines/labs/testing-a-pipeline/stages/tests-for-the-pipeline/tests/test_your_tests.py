import sys

import pytest

pytest_plugins = ["pytester"]

# The modules a run of your tests imports, forgotten after it so the next run starts afresh.
MODULES = ["weather", "daily", "rain", "test_pipeline", "conftest"]

# A conftest that gives your tests the Spark session these tests run in.
CONFTEST = """
import pytest
from pyspark.sql import SparkSession


@pytest.fixture(scope="session")
def spark_session():
    return SparkSession.getActiveSession()
"""

# Each run counts outcomes, with no cache and no hunt for unraisable exceptions in the garbage.
OPTIONS = [
    "-q",
    "--tb=no",
    "-p",
    "no:cacheprovider",
    "-p",
    "no:unraisableexception",
    "-p",
    "sulba_fixtures",
]


def first_failure(recorder):
    """The first of your tests that failed, and the first line of its error, or None."""
    failures = recorder.getfailures()
    if not failures:
        return None
    report = failures[0]
    crash = getattr(report.longrepr, "reprcrash", None)
    error = crash.message.splitlines()[0] if crash else "it failed"
    return f"{report.nodeid.split('::')[-1]}, with {error}"


@pytest.mark.id("tst_1t25ss")
def test_pass_on_your_pipeline(pytester, pytestconfig, monkeypatch, spark):
    """Your tests pass on your pipeline"""
    root = pytestconfig.rootpath
    (pytester.path / "test_pipeline.py").write_text(
        (root / "test_pipeline.py").read_text()
    )
    (pytester.path / "conftest.py").write_text(CONFTEST)
    monkeypatch.chdir(root)
    try:
        recorder = pytester.inline_run(
            *OPTIONS, str(pytester.path / "test_pipeline.py")
        )
    finally:
        for name in MODULES:
            sys.modules.pop(name, None)
    passed, _, failed = recorder.countoutcomes()
    assert failed == 0, (
        f"{failed} failed on your pipeline, the first {first_failure(recorder)}"
    )
    assert passed > 0, "No tests of yours ran"
