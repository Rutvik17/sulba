import json
import math
from pathlib import Path

import pytest

from power import detectable, questions_needed

RECORDED = json.loads(Path("references/power.json").read_text(encoding="utf-8"))[
    "cases"
]


@pytest.mark.id("tst_vaaua1")
def test_detectable():
    """The effect at which statsmodels' NormalIndPower gives a one-sided test its power"""
    for case in RECORDED:
        error = 1 / math.sqrt(case["questions"])
        found = detectable(error, case["alpha"], case["power"])
        assert found == pytest.approx(case["effect"], rel=1e-9)


@pytest.mark.id("tst_nxyfm9")
def test_half_the_time():
    """At a power of one half, the drop at which the test's bound reaches zero"""
    assert detectable(0.02, 0.05, 0.5) == pytest.approx(1.6448536269514722 * 0.02)
    assert detectable(0.02, 0.1, 0.5) == pytest.approx(1.2815515655446004 * 0.02)


@pytest.mark.id("tst_qa5dfo")
def test_questions_needed():
    """The fewest questions whose standard error lets the test find the drop"""
    for drop in (0.02, 0.05, 0.1, 0.3):
        found = questions_needed(0.03, 300, drop, 0.05, 0.8)
        reach = detectable(0.03, 0.05, 0.8)
        assert reach * math.sqrt(300 / found) <= drop
        assert found == 1 or reach * math.sqrt(300 / (found - 1)) > drop
