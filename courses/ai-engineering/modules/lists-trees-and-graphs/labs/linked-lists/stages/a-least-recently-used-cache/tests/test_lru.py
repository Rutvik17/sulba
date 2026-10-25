import random
from collections import OrderedDict

import pytest
from lru import Cache

OPERATIONS = 200_000
CAPACITY = 50_000


class Reference:
    """The same cache, on an OrderedDict."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.items = OrderedDict()

    def get(self, key):
        if key not in self.items:
            return -1
        self.items.move_to_end(key)
        return self.items[key]

    def put(self, key, value):
        if key in self.items:
            self.items.move_to_end(key)
        elif len(self.items) == self.capacity:
            self.items.popitem(last=False)
        self.items[key] = value


@pytest.mark.id("tst_6uhfin")
def test_cache():
    """Drops the least recently used key"""
    cache = Cache(2)
    cache.put(1, 1)
    cache.put(2, 2)
    assert cache.get(1) == 1
    cache.put(3, 3)
    assert cache.get(2) == -1
    assert cache.get(3) == 3
    assert cache.get(1) == 1


@pytest.mark.id("tst_lew3bb")
def test_edges():
    """Updates a key in place, counts a put as a use, and keeps one key"""
    cache = Cache(2)
    cache.put(1, 1)
    cache.put(2, 2)
    cache.put(1, 10)
    cache.put(3, 3)
    assert (cache.get(1), cache.get(2), cache.get(3)) == (10, -1, 3)
    single = Cache(1)
    single.put(1, 1)
    single.put(2, 2)
    assert (single.get(1), single.get(2)) == (-1, 2)
    assert Cache(3).get(7) == -1


@pytest.mark.id("tst_275wu7")
def test_reference():
    """Matches the same cache on an OrderedDict"""
    rng = random.Random(87)
    for _ in range(100):
        capacity = rng.randint(1, 5)
        cache, reference = Cache(capacity), Reference(capacity)
        for _ in range(60):
            key = rng.randint(0, 8)
            if rng.random() < 0.5:
                assert cache.get(key) == reference.get(key)
            else:
                value = rng.randint(0, 99)
                cache.put(key, value)
                reference.put(key, value)


@pytest.mark.id("tst_qu42ty")
def test_long():
    """Puts and gets many keys in time"""
    rng = random.Random(88)
    cache, reference = Cache(CAPACITY), Reference(CAPACITY)
    for key in range(CAPACITY):
        cache.put(key, key)
        reference.put(key, key)
    got = []
    for step in range(OPERATIONS - CAPACITY):
        key = rng.randint(0, 2 * CAPACITY)
        if step % 2:
            got.append(cache.get(key) == reference.get(key))
        else:
            cache.put(key, step)
            reference.put(key, step)
    assert all(got)
