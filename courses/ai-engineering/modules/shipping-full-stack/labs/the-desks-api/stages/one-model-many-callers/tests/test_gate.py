import asyncio

import pytest

from gate import Busy, Gate, within


@pytest.mark.id("tst_pha6v8")
def test_replies_run_a_few_at_once(loop):
    """At most running replies at once; the next waits in line until one leaves"""
    gate = Gate(running=2, waiting=4, seconds=60)
    started = []

    async def reply(name, seconds):
        await gate.enter()
        started.append((name, loop.time()))
        try:
            await asyncio.sleep(seconds)
        finally:
            gate.leave()

    async def go():
        await asyncio.gather(
            reply("a", 10), reply("b", 30), reply("c", 5), reply("d", 5)
        )

    loop.run_until_complete(go())
    assert started == [("a", 0), ("b", 0), ("c", 10), ("d", 15)]


@pytest.mark.id("tst_gh125h")
def test_a_full_line_is_busy(loop):
    """Past the line's end a caller gets Busy, with the seconds to come back in"""
    gate = Gate(running=1, waiting=1, seconds=42.5)

    async def go():
        await gate.enter()
        waiting = asyncio.ensure_future(gate.enter())
        await asyncio.sleep(0)
        with pytest.raises(Busy) as busy:
            await gate.enter()
        gate.leave()
        await waiting
        return busy.value.retry_after

    assert loop.run_until_complete(go()) == 43


@pytest.mark.id("tst_iofu6j")
def test_a_caller_who_leaves_the_line(loop):
    """A caller who leaves while waiting gives up their place in line"""
    gate = Gate(running=1, waiting=1, seconds=60)

    async def go():
        await gate.enter()
        waiting = asyncio.ensure_future(gate.enter())
        await asyncio.sleep(1)
        waiting.cancel()
        with pytest.raises(asyncio.CancelledError):
            await waiting
        # The line is empty again, so the next caller waits rather than being turned away.
        again = asyncio.ensure_future(gate.enter())
        await asyncio.sleep(1)
        assert not again.done()
        gate.leave()
        await again

    loop.run_until_complete(go())


@pytest.mark.id("tst_qc85ps")
def test_a_reply_past_its_time(loop):
    """A reply's events stop at its time limit, and the events are closed"""
    closed = []

    async def events():
        try:
            for n in range(10):
                await asyncio.sleep(4)
                yield n
        finally:
            closed.append(loop.time())

    async def go():
        got = []
        with pytest.raises(TimeoutError):
            async for event in within(events(), 10):
                got.append(event)
        return got

    assert loop.run_until_complete(go()) == [0, 1]
    assert closed == [10]


@pytest.mark.id("tst_g53pde")
def test_a_reply_in_time(loop):
    """A reply that ends in time gives every event"""

    async def events():
        for n in range(3):
            await asyncio.sleep(2)
            yield n

    async def go():
        return [event async for event in within(events(), 10)]

    assert loop.run_until_complete(go()) == [0, 1, 2]
