import json
import math
from pathlib import Path

import pytest

from costs import cost, interval, per_task, quantile

RECORDED = json.loads(Path("references/quantiles.json").read_text(encoding="utf-8"))[
    "cases"
]


def run(variant, task, seconds, prompt, completion):
    return {
        "variant": variant,
        "task": task,
        "seconds": f"{seconds:.3f}",
        "prompt_tokens": str(prompt),
        "completion_tokens": str(completion),
    }


@pytest.mark.id("tst_f1vxw2")
def test_a_runs_cost():
    """A run's seconds, or its tokens of prompt and of reply together"""
    one = run("agent", "t1", 61.5, 3000, 250)
    assert cost(one, "seconds") == 61.5
    assert cost(one, "tokens") == 3250
    with pytest.raises(ValueError):
        cost(one, "requests")


@pytest.mark.id("tst_7zurnl")
def test_each_tasks_median():
    """Each task's median over the variant's trials of it"""
    runs = [
        run("agent", "t1", 10, 100, 10),
        run("agent", "t1", 30, 300, 10),
        run("agent", "t1", 20, 200, 10),
        run("agent", "t2", 5, 50, 5),
        run("agent", "t2", 7, 70, 5),
        run("proposals", "t1", 99, 999, 9),
    ]
    assert per_task(runs, "agent", "seconds") == {"t1": 20, "t2": 6}
    assert per_task(runs, "agent", "tokens") == {"t1": 210, "t2": 65}
    assert per_task(runs, "proposals", "seconds") == {"t1": 99}


@pytest.mark.id("tst_ywg8kl")
def test_numpys_quantile():
    """The quantile NumPy gives by default, for each recorded case"""
    for case in RECORDED:
        assert quantile(case["values"], case["p"]) == pytest.approx(
            case["quantile"], rel=1e-12, abs=1e-12
        )


@pytest.mark.id("tst_o4o2nr")
def test_scipys_interval():
    """The interval SciPy's quantile_test gives, for each recorded case, with nan for an end
    there aren't enough values for"""
    for case in RECORDED:
        low, high = interval(case["values"], case["p"], case["confidence"])
        for got, expected in ((low, case["low"]), (high, case["high"])):
            if expected is None:
                assert math.isnan(got)
            else:
                assert got == expected


@pytest.mark.id("tst_ar45au")
def test_more_confidence():
    """More confidence gives an interval that holds the one with less"""
    values = [float(n * n % 97) for n in range(60)]
    low, high = interval(values, 0.5, 0.99)
    narrow_low, narrow_high = interval(values, 0.5, 0.8)
    assert low <= narrow_low <= quantile(values, 0.5) <= narrow_high <= high
