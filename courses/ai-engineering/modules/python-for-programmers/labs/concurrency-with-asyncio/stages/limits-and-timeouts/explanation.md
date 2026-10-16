```python
async def check_limited(codes, registry, limit):
    gate = asyncio.Semaphore(limit)

    async def limited(code):
        async with gate:
            return await check_code(code, registry)

    return await asyncio.gather(*(limited(code) for code in codes))
```

Every code's task starts at once and waits at the gate, so the lookups go out `limit` at a time, each round as long as one lookup. `async with gate:` gives the slot back however the block ends, an error or a cancellation included, as `acquire()` and a `release()` in a `finally` clause would.

The timeout cancels the lookup it interrupts, so the hung lookup ends when the seconds have passed, and the stand-in's count comes back down. The registry may still answer it later; the service has stopped listening. The error is raised as the `async with` block ends, so the `try` goes around the block.
