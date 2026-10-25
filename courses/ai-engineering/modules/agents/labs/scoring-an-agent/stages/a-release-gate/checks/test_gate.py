import math
import statistics

import pytest

from gate import gate


def runs(variant, done, seconds=60.0, trials=5, first=0):
    return [
        {
            "variant": variant,
            "task": f"t{first + n}",
            "outcome": "done" if trial < each else "cited no passage",
            "seconds": f"{seconds + n % 7:.3f}",
            "prompt_tokens": "3000",
            "completion_tokens": "200",
        }
        for n, each in enumerate(done)
        for trial in range(trials)
    ]


@pytest.mark.id("tst_4k8spf")
def test_compared_task_by_task():
    """The candidate is compared with the current agent task by task, so that one task's
    difference among many isn't lost in the spread between tasks"""
    done = [5, 0] * 60
    less = list(done)
    less[0] = 4
    verdict = gate(
        runs("agent", done) + runs("candidate", less),
        "agent",
        "candidate",
        k=5,
        tolerance=0.05,
        seconds=120,
    )
    differences = [-1.0] + [0.0] * 119
    margin = 1.959964 * statistics.stdev(differences) / math.sqrt(120)
    assert verdict.difference.value == pytest.approx(-1 / 120)
    assert verdict.difference.low == pytest.approx(-1 / 120 - margin, rel=1e-6)
    assert verdict.difference.high == pytest.approx(-1 / 120 + margin, rel=1e-6)
    assert verdict.ship


@pytest.mark.id("tst_fitby9")
def test_held_only_for_being_worse():
    """A candidate is held for its pass^k only when it may be worse, however much better it is,
    and at the tolerance given"""
    done = [5, 3, 0, 4] * 10
    better = [5] * 40
    verdict = gate(
        runs("agent", done) + runs("candidate", better),
        "agent",
        "candidate",
        k=2,
        tolerance=0.0,
        seconds=120,
    )
    assert verdict.held == ()
    assert verdict.difference.low > 0
    worse = gate(
        runs("agent", better) + runs("candidate", done),
        "agent",
        "candidate",
        k=2,
        tolerance=0.9,
        seconds=120,
    )
    assert worse.ship
    assert worse.difference.low < -0.05


@pytest.mark.id("tst_mvzf8v")
def test_a_tail_it_cant_bound():
    """A candidate whose 90th percentile has no high end, on too few tasks to give one, is held
    for its seconds"""
    done = [5] * 20
    verdict = gate(
        runs("agent", done) + runs("candidate", done, seconds=1),
        "agent",
        "candidate",
        k=5,
        tolerance=0.05,
        seconds=120,
    )
    assert math.isnan(verdict.tail.high)
    assert verdict.held == ("seconds",)


@pytest.mark.id("tst_zcbnfl")
def test_the_same_tasks_and_trials():
    """Agents that ran different tasks, or a task a different number of times, or fewer than k
    times, can't be compared"""
    done = [5, 3, 0, 4] * 10
    options = {"k": 5, "tolerance": 0.05, "seconds": 120}
    with pytest.raises(ValueError):
        gate(
            runs("agent", done) + runs("candidate", done[:-1]),
            "agent",
            "candidate",
            **options,
        )
    with pytest.raises(ValueError):
        gate(
            runs("agent", done) + runs("candidate", done, first=1),
            "agent",
            "candidate",
            **options,
        )
    with pytest.raises(ValueError):
        gate(
            runs("agent", done) + runs("candidate", [3] * 40, trials=4),
            "agent",
            "candidate",
            **options,
        )
    with pytest.raises(ValueError):
        gate(
            runs("agent", [3] * 40, trials=4) + runs("candidate", [3] * 40, trials=4),
            "agent",
            "candidate",
            **options,
        )
