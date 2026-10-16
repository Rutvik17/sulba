The assistant's tests gave its lookups only known codes, against a registry that answered every one quickly and dropped none.

---

Each problem was about where a wait, an error or a slot belongs: a lookup has to be awaited to run; a slot is given back by `async with`, which an error can't skip; and an error or a timeout that belongs to one code is caught inside that code's coroutine, so `gather` still collects every other answer. A failure kept to its own task leaves the rest of the day to finish.
