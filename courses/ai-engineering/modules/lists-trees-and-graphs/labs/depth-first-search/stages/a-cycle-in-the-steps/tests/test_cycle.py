import random

import pytest

from cycle import cycle

STEPS = 100_000


def has_cycle(needs):
    """Whether the job has a cycle, by taking away steps no other step needs until none are left."""
    steps = set(needs) | {step for each in needs.values() for step in each}
    needed = dict.fromkeys(steps, 0)
    for each in needs.values():
        for step in each:
            needed[step] += 1
    free = [step for step in steps if needed[step] == 0]
    taken = 0
    while free:
        step = free.pop()
        taken += 1
        for other in needs.get(step, []):
            needed[other] -= 1
            if needed[other] == 0:
                free.append(other)
    return taken < len(steps)


def is_cycle(needs, found):
    """Whether found is a cycle of the job: each step needs the next, and the last is the first."""
    return (
        len(found) >= 2
        and found[0] == found[-1]
        and len(set(found[:-1])) == len(found) - 1
        and all(found[n + 1] in needs.get(found[n], []) for n in range(len(found) - 1))
    )


@pytest.mark.id("tst_7dku27")
def test_cycle():
    """Finds a cycle, or None when there's none"""
    needs = {"a": ["b"], "b": ["c"], "c": ["a"]}
    assert is_cycle(needs, cycle(needs))
    assert cycle({"a": ["b"], "b": []}) is None


@pytest.mark.id("tst_ws34ui")
def test_edges():
    """Handles no steps, a step that needs itself, and needs without lists of their own"""
    assert cycle({}) is None
    assert cycle({"a": ["a"]}) == ["a", "a"]
    assert cycle({"a": ["b", "c"], "b": ["c"]}) is None
    needs = {"a": ["b"], "b": ["c", "d"], "d": ["b"]}
    assert is_cycle(needs, cycle(needs))


@pytest.mark.id("tst_jdle1i")
def test_random():
    """Finds a cycle exactly when taking away free steps leaves some, on random jobs"""
    rng = random.Random(731)
    for _ in range(500):
        count = rng.randint(1, 7)
        needs = {
            step: [other for other in range(count) if rng.random() < 0.25]
            for step in range(count)
            if rng.random() < 0.9
        }
        found = cycle(needs)
        if has_cycle(needs):
            assert is_cycle(needs, found)
        else:
            assert found is None


@pytest.mark.id("tst_wh52aa")
def test_long():
    """Finds a long cycle, and none in a long chain, in time"""
    needs = {step: [step + 1] for step in range(STEPS - 1)}
    assert cycle(needs) is None
    needs[STEPS - 1] = [0]
    found = cycle(needs)
    assert is_cycle(needs, found)
    assert len(found) == STEPS + 1
