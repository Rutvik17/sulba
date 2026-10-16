import asyncio

import pytest

from fetch import registered_all, stalls


@pytest.mark.id("tst_loop01")
def test_concurrent(loop):
    """Asks about eight codes at a time"""
    codes = [f"S{i:03d}" for i in range(100)]
    assert loop.run_until_complete(registered_all(codes, 8)) == [True] * 100
    assert loop.time() == 3.25


@pytest.mark.id("tst_loop02")
def test_timeout(loop):
    """Times out a slow answer, on a clock of its own"""

    async def slow():
        async with asyncio.timeout(1):
            await asyncio.sleep(60)

    with pytest.raises(TimeoutError):
        loop.run_until_complete(slow())
    assert loop.time() == 1


@pytest.mark.id("tst_loop03")
def test_task_group(loop):
    """Gathers a task group's results"""

    async def main():
        async with asyncio.TaskGroup() as group:
            tasks = [group.create_task(asyncio.sleep(i, result=i)) for i in range(4)]
        return [task.result() for task in tasks]

    assert loop.run_until_complete(main()) == [0, 1, 2, 3]
    assert loop.time() == 3


@pytest.mark.id("tst_loop04")
def test_stalls(loop):
    """Stops code that waits forever"""
    loop.run_until_complete(stalls())
