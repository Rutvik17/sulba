import random
import string

import pytest
from ladder import ladder

OTHERS = 5_000
LETTERS = 6


def apart(first, second):
    """Whether the two words differ in exactly one place."""
    return sum(a != b for a, b in zip(first, second)) == 1


def searched(start, end, words):
    """The shortest ladder's words, by a search that compares each word with every other."""
    words = list(dict.fromkeys(words))
    if end not in words:
        return 0
    level, seen, count = [start], {start}, 1
    while level:
        if end in level:
            return count
        level = [
            word
            for word in words
            if word not in seen and any(apart(word, other) for other in level)
        ]
        seen.update(level)
        count += 1
    return 0


@pytest.mark.id("tst_dv0cxr")
def test_ladder():
    """Counts the words of the shortest ladder"""
    words = ["cord", "card", "ward", "warm", "word", "worm", "corm", "wore", "core"]
    assert ladder("cold", "warm", words) == 5


@pytest.mark.id("tst_nketa8")
def test_edges():
    """Gives 0 when end isn't among the words or can't be reached, and 2 for one step"""
    assert ladder("cold", "warm", ["cord", "card", "ward"]) == 0
    assert ladder("abc", "xyz", ["abz", "xyz"]) == 0
    assert ladder("hot", "hit", ["hit"]) == 2
    assert ladder("hot", "dog", ["hot", "dot", "dog"]) == 3
    assert ladder("a", "c", ["b", "c"]) == 2


@pytest.mark.id("tst_trbwfi")
def test_random():
    """Matches a search that compares every pair of words, on random lists"""
    rng = random.Random(105)
    for _ in range(300):
        size = rng.randint(1, 4)

        def word():
            return "".join(rng.choices("abc", k=size))

        words = [word() for _ in range(rng.randint(1, 20))]
        start, end = word(), rng.choice(words)
        if start != end:
            assert ladder(start, end, words) == searched(start, end, words)


@pytest.mark.id("tst_rbgj9f")
def test_long():
    """Finds the shortest ladder among many words in time"""
    rng = random.Random(106)
    others = [
        "".join(rng.choices(string.ascii_lowercase, k=LETTERS)) for _ in range(OTHERS)
    ]
    rungs = ["z" * place + "a" * (LETTERS - place) for place in range(1, LETTERS + 1)]
    words = others + rungs
    rng.shuffle(words)
    assert ladder("a" * LETTERS, "z" * LETTERS, words) == LETTERS + 1
