import math
import statistics

import pytest

from scorecard import costs, percentile, reliability


def run(
    task, outcome="done", seconds=60.0, prompt=3000, completion=200, variant="agent"
):
    return {
        "variant": variant,
        "task": task,
        "outcome": outcome,
        "seconds": f"{seconds:.3f}",
        "prompt_tokens": str(prompt),
        "completion_tokens": str(completion),
    }


def tasks(done):
    """Five trials of each task, the first done of them done."""
    return [
        run(f"t{n}", "done" if trial < each else "cited no passage")
        for n, each in enumerate(done)
        for trial in range(5)
    ]


@pytest.mark.id("tst_02cqbl")
def test_pass_hat_k_from_the_trials():
    """pass^k is the chance that k of a task's trials drawn without replacement were all done"""
    runs = tasks([4, 3, 5, 0])
    assert reliability(runs, "agent", 5).value == pytest.approx(0.25)
    expected = (
        (math.comb(4, 2) + math.comb(3, 2) + math.comb(5, 2)) / math.comb(5, 2) / 4
    )
    assert reliability(runs, "agent", 2).value == pytest.approx(expected)


@pytest.mark.id("tst_dkw07u")
def test_a_95_percent_interval():
    """The interval is the mean plus or minus 1.96 standard errors"""
    runs = tasks([5, 0, 0, 5, 5, 0, 5, 5, 0, 5])
    estimate = reliability(runs, "agent", 3)
    values = [1.0, 0, 0, 1, 1, 0, 1, 1, 0, 1]
    margin = 1.959964 * statistics.stdev(values) / math.sqrt(len(values))
    assert estimate.high - estimate.value == pytest.approx(margin, rel=1e-6)
    assert estimate.value - estimate.low == pytest.approx(margin, rel=1e-6)


@pytest.mark.id("tst_titsli")
def test_a_percentile_of_tasks():
    """A task's trials count once, by their median, in a percentile and its interval"""
    runs = [
        run(f"t{n}", seconds=20 + 3 * n + trial)
        for n in range(40)
        for trial in (-1, 0, 0, 1, 2)
    ]
    medians = [20.0 + 3 * n for n in range(40)]
    estimate = percentile(runs, "agent", "seconds", 0.9)
    assert estimate.value == pytest.approx(0.9 * medians[35] + 0.1 * medians[36])
    assert (estimate.low, estimate.high) == (medians[31], medians[39])


@pytest.mark.id("tst_dljy4e")
def test_failed_runs_cost_too():
    """A run that failed costs its seconds and tokens, and a task never done has a cost"""
    runs = [run("t1", "done", 40), run("t1", "error", 200), run("t1", "done", 60)]
    runs += [run("t2", "opened 0 tickets", 90), run("t2", "opened 0 tickets", 110)]
    assert costs(runs, "agent", "seconds") == {"t1": 60, "t2": 100}
