Keep the times of the window's requests and retries in two slices, oldest first. Before you count, drop the times at the front that are `window` old or more.

---

A retry is allowed when `len(retries)+1` is no more than `float64(floor) + ratio*float64(len(requests))`.

---

In `RetryWithin`, work out the wait and check it against the deadline first, then ask the budget, then wait, so a refused retry costs the caller no time.
