```python
async def check_code(code, registry):
    if await registry.lookup(code):
        return None
    return f"No patient has the code {code!r}"


async def check_codes(codes, registry):
    return [await check_code(code, registry) for code in codes]
```

`await` gives back control to the event loop until the lookup's answer comes, so the loop can run other coroutines in the meantime. Here there are none, so `check_codes` waits out the registry's latency once for each code: each `await` finishes before the next lookup starts. Making them at once takes tasks, in the next stage.

A coroutine that's never awaited does nothing, and Python warns, when it's thrown away, that it was never awaited. `if registry.lookup(code):` without `await` tests the coroutine object itself, which is true, so every code would pass.
