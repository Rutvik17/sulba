`self.places`, an `asyncio.Semaphore(running)`, holds the running places: `acquire()` waits for one, `release()` gives one back, and `locked()` says whether none is free. Count the callers in line yourself, in `self.queued`.

---

Count a caller into the line before awaiting `acquire()`, and out of it in a `finally`, so that a caller whose wait is cancelled is counted out too.

---

`asyncio.wait_for(anext(events), timeout)` raises `TimeoutError` when the next event takes longer than `timeout`. Give it the time left until the deadline, from `asyncio.get_running_loop().time()`, rather than the whole `seconds` each time.
