The tasks come after the tasks they wait for, so one pass in order can work out each task's end: the latest end of the tasks it waits for, plus its own days.

---

`random.Random(seed).triangular(low, high, mode)` takes the mode last. A run is a dict of each task's drawn days, and its finish is `finish(tasks, run)`.
