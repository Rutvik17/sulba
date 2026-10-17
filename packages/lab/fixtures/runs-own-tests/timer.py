import asyncio


async def answer_after(seconds, value):
    """value, once the seconds have passed."""
    await asyncio.sleep(seconds)
    return value
