A day brings hundreds of codes, and one lookup after another adds up all their waits. The registry can answer many lookups at once, so the service makes them at once, and waits for all of them together. Write:

```
check_at_once(codes, registry) -> each code's check, in order, with every lookup
    made at once
check_all(codes, registry) -> the same in a task group: when lookups fail, an
    ExceptionGroup of their errors, with the lookups still waiting cancelled
check_each(codes, registry) -> each code's check, in order, with every lookup made at
    once, and this message for a lookup that raised ConnectionError:
    The registry couldn't be reached for 'S00002'
```

A `Registry` made with `failing={"S00002"}` raises `ConnectionError` for that code, and one made with `slow={"S00004": 60}` takes that many seconds over it.

`await asyncio.gather(*coroutines)` runs coroutines at once and gives their results in their order, as JavaScript's `Promise.all` does. When one raises, `gather` raises its error, and the others go on running, as with `Promise.all`. With `return_exceptions=True`, it gives each error among the results instead, as `Promise.allSettled` gives each rejection. An `async with asyncio.TaskGroup() as group:` block waits for each task made with `group.create_task(coroutine)`. When a task fails, the group cancels the tasks still waiting, where `Promise.all` leaves them running, and raises the errors together in an `ExceptionGroup`.
