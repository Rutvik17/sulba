The registry's terms let the clinic make a few lookups at a time, not hundreds, and a lookup sometimes hangs. The service holds itself to a limit, and gives up on a lookup that takes too long. Write:

```
check_limited(codes, registry, limit) -> each code's check, in order, with no more than
    limit lookups at a time
check_in_time(code, registry, seconds) -> the code's check, or this message when its
    lookup takes longer than seconds:
    The registry took too long for 'S00002'
```

`asyncio.Semaphore(limit)` lets `limit` tasks at a time through `async with gate:`, and holds the others at it until one leaves. `async with asyncio.timeout(seconds):` cancels what its block awaits once the seconds have passed, and raises `TimeoutError` as it leaves the block. Both are asynchronous context managers, which `async with` enters and leaves with `await`.
