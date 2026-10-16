```python
async def check_all(codes, registry):
    async with asyncio.TaskGroup() as group:
        tasks = [group.create_task(check_code(code, registry)) for code in codes]
    return [task.result() for task in tasks]
```

A task starts its coroutine on the event loop as soon as the loop is free, so every lookup is under way before any has answered, and all of them take as long as one. `gather` makes a task of each coroutine it's given, the same way.

When a lookup fails, `gather` raises at once and leaves the other lookups running, with nothing waiting for their answers. A task group cancels them, so the slow lookup ends when the failing one does, and its `finally` clauses still run: the stand-in's count of lookups in progress comes back down. A cancelled task gets `asyncio.CancelledError` at the `await` it was waiting at.
