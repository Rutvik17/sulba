import asyncio
import heapq

import pytest

from lookups import Registry, check_day

CODES = [f"S{i:05d}" for i in range(100)]


def finished(seconds, limit):
    """When lookups taking these seconds have all ended, limit at a time, each started as
    soon as a slot frees."""
    slots = [0.0] * limit
    for each in seconds:
        heapq.heappush(slots, heapq.heappop(slots) + each)
    return max(slots)


class Unreadable(Registry):
    """A registry whose reply about one code can't be read."""

    async def lookup(self, code):
        known = await super().lookup(code)
        if code == "S00005":
            raise ValueError("The registry's reply couldn't be read")
        return known


@pytest.mark.id("tst_fa578y")
def test_limit(loop, record_property):
    """Keeps to the limit, and fills each slot as it frees"""
    registry = Registry(CODES, slow={CODES[0]: 2})
    checks = loop.run_until_complete(check_day(CODES, registry, 8, 5))
    record_property("note", f"{registry.most} at a time, {loop.time():g} seconds")
    assert checks == [None] * len(CODES)
    assert registry.most <= 8
    assert loop.time() == finished([2] + [0.25] * 99, 8)


@pytest.mark.id("tst_ei13ke")
def test_timeouts(loop):
    """Times each lookup from when it starts"""
    codes = CODES[:20]
    registry = Registry(codes, slow={codes[0]: 60})
    checks = loop.run_until_complete(check_day(codes, registry, 2, 1.125))
    assert checks == ["The registry took too long for 'S00000'"] + [None] * 19
    assert registry.serving == 0


@pytest.mark.id("tst_xt998d")
def test_nothing_left(loop):
    """Leaves no lookup running"""
    codes = CODES[:20]
    registry = Unreadable(codes)
    with pytest.RaisesGroup(ValueError, allow_unwrapped=True, flatten_subgroups=True):
        loop.run_until_complete(check_day(codes, registry, 4, 5))
    assert not asyncio.all_tasks(loop)
    assert registry.serving == 0
