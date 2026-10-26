import itertools
import random

import pytest

from merging import merged

STREAMS = 2_000
ITEMS = 200_000


@pytest.mark.id("tst_ja7qiw")
def test_merged():
    """Merges sorted lists into one"""
    assert list(merged([[1, 4, 5], [1, 3, 4], [2, 6]])) == [1, 1, 2, 3, 4, 4, 5, 6]


@pytest.mark.id("tst_f7n0ih")
def test_edges():
    """Handles no streams, empty streams and one stream"""
    assert list(merged([])) == []
    assert list(merged([[], []])) == []
    assert list(merged([[], [3, 3], []])) == [3, 3]


@pytest.mark.id("tst_rtmebt")
def test_lazily():
    """Reads each stream only as far as the items it has given need"""
    read = []

    def stream(start):
        for value in itertools.count(start, 2):
            read.append(value)
            yield value

    found = merged([stream(0), stream(1)])
    assert read == []
    assert list(itertools.islice(found, 4)) == [0, 1, 2, 3]
    assert len(read) <= 6


@pytest.mark.id("tst_e9eq8o")
def test_random():
    """Matches sorting every item, on random lists"""
    rng = random.Random(221)
    for _ in range(300):
        lists = [
            sorted(rng.randint(0, 9) for _ in range(rng.randint(0, 6)))
            for _ in range(rng.randint(0, 6))
        ]
        assert list(merged(lists)) == sorted(item for items in lists for item in items)


@pytest.mark.id("tst_uo765k")
def test_endless():
    """Gives the first items of many streams that never end, in time"""
    streams = [itertools.count(start, STREAMS) for start in range(STREAMS)]
    assert list(itertools.islice(merged(streams), ITEMS)) == list(range(ITEMS))
