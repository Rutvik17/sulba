Make one semaphore for the whole call, and an inner coroutine that checks one code inside `async with gate:`. Then gather the inner coroutines.

---

A semaphore made inside the inner coroutine would give each lookup a limit of its own.

---

In `check_in_time`, catch the `TimeoutError` around the `async with asyncio.timeout(seconds):` block, not inside it.
