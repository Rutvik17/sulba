A `HashMap` isn't made for threads: two threads adding at once can lose an addition, or break the map. `java.util.concurrent` has maps and counters that are.

---

`ConcurrentHashMap`'s docs give the pattern for counts: `counts.computeIfAbsent(key, k -> new LongAdder()).increment();`. `sum()` reads a `LongAdder`.

---

`Executors.newVirtualThreadPerTaskExecutor()` starts a thread for each task, as the tests do, and closing it waits for them all.
