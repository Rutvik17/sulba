import random
from collections import Counter

import pytest
from triples import zero_triples

NUMBERS = 1_500


def every_three(numbers):
    """The triples, by trying every three positions."""
    ordered = sorted(numbers)
    found = set()
    for i in range(len(ordered)):
        for j in range(i + 1, len(ordered)):
            for k in range(j + 1, len(ordered)):
                if ordered[i] + ordered[j] + ordered[k] == 0:
                    found.add((ordered[i], ordered[j], ordered[k]))
    return sorted(found)


def by_lookup(numbers):
    """The triples, by fixing a <= b among the values and looking up c = -a - b."""
    counts = Counter(numbers)
    values = sorted(counts)
    found = []
    for i, a in enumerate(values):
        for b in values[i:]:
            c = -a - b
            if c < b:
                break
            if c not in counts:
                continue
            needed = 3 if a == c else 2 if a == b or b == c else 1
            if needed == 1 or counts[b] >= needed:
                found.append((a, b, c))
    return found


@pytest.mark.id("tst_l6ymz7")
def test_triples():
    """Finds every triple that adds up to 0, in order"""
    numbers = [-3, 1, 2, -1, 0, 2, -2, 1]
    assert zero_triples(numbers) == [(-3, 1, 2), (-2, 0, 2), (-2, 1, 1), (-1, 0, 1)]


@pytest.mark.id("tst_u7aad4")
def test_repeats():
    """Gives each triple once, and uses a number twice only if it appears twice"""
    assert zero_triples([0, 0, 0, 0]) == [(0, 0, 0)]
    assert zero_triples([-2, 1]) == []
    assert zero_triples([-2, 1, 1, 1]) == [(-2, 1, 1)]
    assert zero_triples([-2, 1, 3]) == []
    assert zero_triples([]) == []


@pytest.mark.id("tst_inbo2u")
def test_every_three():
    """Matches trying every three positions"""
    rng = random.Random(30)
    for _ in range(200):
        numbers = [rng.randint(-6, 6) for _ in range(rng.randint(0, 11))]
        assert zero_triples(numbers) == every_three(numbers)


@pytest.mark.id("tst_j43p3c")
def test_long():
    """Finds the triples in a long list in time"""
    rng = random.Random(31)
    numbers = [rng.randint(-2000, 2000) for _ in range(NUMBERS)]
    assert zero_triples(numbers) == by_lookup(numbers)
