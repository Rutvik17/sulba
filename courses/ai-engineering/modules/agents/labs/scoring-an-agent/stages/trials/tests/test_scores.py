import math
import statistics

import pytest

from scores import Score, pass_at_k, pass_hat_k, score, trials


@pytest.mark.id("tst_auhaqf")
def test_one_task():
    """For a task of n trials, c of which did it, pass@k is the chance that one of k of them
    did, and pass^k the chance that all k did"""
    assert pass_at_k(5, 3, 2) == pytest.approx(0.9)
    assert pass_hat_k(5, 3, 2) == pytest.approx(0.3)
    assert pass_at_k(5, 3, 1) == pytest.approx(0.6) == pass_hat_k(5, 3, 1)
    assert pass_hat_k(5, 5, 5) == 1.0 and pass_at_k(5, 0, 3) == 0.0
    assert pass_at_k(4, 2, 3) == 1.0 and pass_hat_k(4, 2, 3) == 0.0


@pytest.mark.id("tst_yw2198")
def test_out_of_range():
    """k runs from 1 to the task's trials, and c from 0 to them; anything else is an error"""
    for n, c, k in [(5, 3, 0), (5, 3, 6), (5, 6, 2), (5, -1, 2)]:
        with pytest.raises(ValueError):
            pass_at_k(n, c, k)
        with pytest.raises(ValueError):
            pass_hat_k(n, c, k)


@pytest.mark.id("tst_j2zm88")
def test_counting_trials():
    """Each task's trials by one variant, and how many did the task"""
    rows = [
        {"variant": "agent", "task": "t1", "outcome": "done"},
        {"variant": "agent", "task": "t1", "outcome": "cited no passage"},
        {"variant": "agent", "task": "t2", "outcome": "done"},
        {"variant": "proposals", "task": "t1", "outcome": "done"},
    ]
    assert trials(rows, "agent") == {"t1": (2, 1), "t2": (1, 1)}
    assert trials(rows, "proposals") == {"t1": (1, 1)}


@pytest.mark.id("tst_f1w0ze")
def test_over_tasks():
    """A score is each task's averaged over the tasks, so a task with more trials counts no
    more than one with fewer"""
    counts = {"t1": (10, 10), "t2": (2, 0)}
    assert score(counts, 1).value == pytest.approx(0.5)
    assert score(counts, 2).value == pytest.approx(0.5)
    assert score(counts, 2, every=False).value == pytest.approx(0.5)


@pytest.mark.id("tst_2u212y")
def test_the_interval():
    """The interval is the mean plus or minus z standard errors of the tasks' scores, z for the
    confidence"""
    counts = {"t1": (5, 5), "t2": (5, 3), "t3": (5, 1), "t4": (5, 0)}
    values = [pass_hat_k(5, c, 2) for _, c in counts.values()]
    mean = statistics.mean(values)
    margin = 1.959963984540054 * statistics.stdev(values) / math.sqrt(4)
    got = score(counts, 2)
    assert isinstance(got, Score)
    assert got.value == pytest.approx(mean)
    assert got.low == pytest.approx(mean - margin)
    assert got.high == pytest.approx(mean + margin)
    narrower = score(counts, 2, confidence=0.9)
    assert narrower.high - narrower.low < got.high - got.low
