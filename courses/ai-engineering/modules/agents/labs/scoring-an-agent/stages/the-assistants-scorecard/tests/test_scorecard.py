import pytest

from costs import interval, quantile
from scorecard import costs, percentile, reliability, scorecard


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


@pytest.mark.id("tst_dxelnx")
def test_tasks_done_every_time_or_never():
    """pass^k of tasks done on every trial or on none"""
    runs = [run("t1") for _ in range(5)]
    runs += [run("t2", "cited no passage") for _ in range(5)]
    runs += [run("t3") for _ in range(5)]
    for k in (1, 3):
        estimate = reliability(runs, "agent", k)
        assert estimate.value == pytest.approx(2 / 3)
        assert estimate.low < estimate.value < estimate.high


@pytest.mark.id("tst_q7x4ze")
def test_each_tasks_cost():
    """Each task's median seconds and tokens"""
    runs = [run("t1", seconds=s, prompt=1000 * s) for s in (30, 10, 20)]
    runs += [run("t2", seconds=s) for s in (5, 7)]
    assert costs(runs, "agent", "seconds") == {"t1": 20, "t2": 6}
    assert costs(runs, "agent", "tokens") == {"t1": 20200, "t2": 3200}


@pytest.mark.id("tst_mfwovc")
def test_a_percentile():
    """A percentile over the tasks, with its interval"""
    seconds = [float(10 + n * n % 37) for n in range(40)]
    runs = [run(f"t{n}", seconds=s) for n, s in enumerate(seconds)]
    estimate = percentile(runs, "agent", "seconds", 0.9)
    assert estimate.value == pytest.approx(quantile(seconds, 0.9))
    assert (estimate.low, estimate.high) == interval(seconds, 0.9, 0.95)


@pytest.mark.id("tst_wn8kit")
def test_the_scorecard():
    """A line for each agent, each number within its interval"""
    runs = [
        run(
            f"t{n}",
            "done" if (n + trial) % 3 else "error",
            30 + n + trial,
            variant=variant,
        )
        for variant in ("agent", "proposals")
        for n in range(40)
        for trial in range(5)
    ]
    card = scorecard(runs, ["agent", "proposals"], 5)
    assert list(card) == ["agent", "proposals"]
    for line in card.values():
        assert list(line) == [
            "pass^1",
            "pass^5",
            "median seconds",
            "p90 seconds",
            "median tokens",
            "p90 tokens",
        ]
        for estimate in line.values():
            assert estimate.low <= estimate.value <= estimate.high
