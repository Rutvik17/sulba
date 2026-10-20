import numpy as np
import pytest

from release import Line, line, report


def passing(*values):
    return {"cites": values[0], "finished": values[1]}


RESULTS = {
    "q1": passing(True, True),
    "q2": passing(True, False),
    "q3": passing(True, True),
    "q4": passing(False, True),
    "q5": passing(True, True),
    "q6": passing(True, True),
}
PAGES = {
    "q1": "va-1",
    "q2": "va-1",
    "q3": "va-2",
    "q4": "ssa-1",
    "q5": "ssa-2",
    "q6": "ssa-3",
}
SERVICES = {name: page.split("-")[0] for name, page in PAGES.items()}


@pytest.mark.id("tst_u0c15h")
def test_lines():
    """Gives a line for all the questions and one for each service"""
    lines = report(RESULTS, PAGES, SERVICES, 0.1, 0.95)
    assert list(lines) == ["all", "ssa", "va"]
    assert all(isinstance(found, Line) for found in lines.values())
    assert [found.questions for found in lines.values()] == [6, 3, 3]


@pytest.mark.id("tst_764upg")
def test_a_line():
    """Gives a group's pass rate, its margin of error and the questions it would need"""
    found = line(np.array([1.0, 0, 1, 1]), ["va-1", "va-2", "va-3", "va-4"], 0.5, 0.95)
    assert found.rate == 0.75
    assert found.questions == 4
    assert 0 < found.margin < 1
    assert found.needed >= 1
