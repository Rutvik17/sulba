A `Semaphore` made with a permit for each running place gives them out: `acquire()` takes one, waiting until one is free, and `release()` gives it back.

---

`new Semaphore(running, true)` is fair: it gives permits to waiting threads in the order they asked.

---

A second semaphore, with a permit for each running place and each place in line, counts who's inside the gate. Its `tryAcquire()` takes a permit without waiting, or returns `false` when there's none.

---

`acquire()` throws `InterruptedException` when the thread is interrupted while it waits, and takes no permit. Give the place in line back before throwing it on.

---

`limit.toSeconds()` rounds down. `limit.toNanosPart()` is what's left over, in nanoseconds.
