`asyncio.gather(*(check_code(code, registry) for code in codes))` passes each coroutine as its own argument.

---

In `check_all`, keep each task `group.create_task` gives you, and read its `result()` after the `async with` block, when every task has finished.

---

With `return_exceptions=True`, test each result with `isinstance(result, ConnectionError)`, and raise any other error again.
