import pytest

from gate import gate


def runs(variant, done, seconds=60.0):
    """Five trials of each task, the first done[n] of task n's done."""
    return [
        {
            "variant": variant,
            "task": f"t{n}",
            "outcome": "done" if trial < each else "cited no passage",
            "seconds": f"{seconds + n % 7:.3f}",
            "prompt_tokens": "3000",
            "completion_tokens": "200",
        }
        for n, each in enumerate(done)
        for trial in range(5)
    ]


DONE = [5, 4, 0, 5, 3, 5, 2, 5, 5, 1] * 4


@pytest.mark.id("tst_ftv057")
def test_two_alike_agents():
    """A candidate that does what the current agent does ships"""
    verdict = gate(
        runs("agent", DONE) + runs("candidate", DONE),
        "agent",
        "candidate",
        k=5,
        tolerance=0.05,
        seconds=120,
    )
    assert verdict.ship
    assert verdict.held == ()
    assert (verdict.difference.value, verdict.difference.low) == (0, 0)


@pytest.mark.id("tst_30vbt8")
def test_a_less_reliable_candidate():
    """A candidate that does fewer tasks every time is held for its pass^k"""
    worse = [min(each, 4) if n % 2 else each for n, each in enumerate(DONE)]
    verdict = gate(
        runs("agent", DONE) + runs("candidate", worse),
        "agent",
        "candidate",
        k=5,
        tolerance=0.05,
        seconds=120,
    )
    assert not verdict.ship
    assert verdict.held == ("pass^k",)
    assert verdict.difference.value < 0


@pytest.mark.id("tst_tl5smo")
def test_a_slow_candidate():
    """A candidate whose 90th percentile of seconds may be over the budget is held for it"""
    verdict = gate(
        runs("agent", DONE) + runs("candidate", DONE, seconds=150),
        "agent",
        "candidate",
        k=5,
        tolerance=0.05,
        seconds=120,
    )
    assert verdict.held == ("seconds",)
    assert verdict.tail.value > 120
