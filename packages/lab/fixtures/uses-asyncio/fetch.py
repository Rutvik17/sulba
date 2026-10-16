"""Asks the clinic's registry about samples' codes, a few at a time."""

import asyncio


async def registered(code):
    """Whether the registry knows code, answered a quarter of a second later."""
    await asyncio.sleep(0.25)
    return code.startswith("S")


async def registered_all(codes, limit):
    """Whether the registry knows each code, asking about at most limit at once."""
    gate = asyncio.Semaphore(limit)

    async def one(code):
        async with gate:
            return await registered(code)

    return await asyncio.gather(*(one(code) for code in codes))


async def stalls():
    """Waits on a future that nothing completes."""
    await asyncio.get_running_loop().create_future()
