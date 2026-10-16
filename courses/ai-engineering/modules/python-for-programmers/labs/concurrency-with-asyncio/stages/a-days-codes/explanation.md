```python
async def check_day(codes, registry, limit, seconds):
    gate = asyncio.Semaphore(limit)

    async def one(code):
        async with gate:
            try:
                return await check_in_time(code, registry, seconds)
            except ConnectionError:
                return f"The registry couldn't be reached for {code!r}"

    async with asyncio.TaskGroup() as group:
        tasks = [group.create_task(one(code)) for code in codes]
    return [task.result() for task in tasks]
```

A code's timeout starts inside `async with gate:`, once its lookup has a slot. Around the gate, the time a code spent waiting would count against its lookup, and the codes at the end of a long day would time out before the registry was asked about them. A lookup that times out is cancelled, and its slot goes to the next code.

Batches of `limit` lookups, each gathered in turn, keep to the limit too, but each batch waits for its slowest lookup while the slots of the fast ones sit empty. A semaphore hands each slot on as soon as it frees.

A dropped lookup's message is given inside its own coroutine, so the other codes keep their answers. Any other error is a bug, and the task group cancels the lookups still going or waiting, then raises it in an `ExceptionGroup`. With `gather`, the error would reach the caller while the other lookups went on, asking the registry about codes whose answers no one would read.
