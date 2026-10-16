Putting the larger digit first isn't enough: for `3` and `30`, which goes first? Compare the two orders the pair can be written in.

---

Sort with a comparison that puts `a` before `b` when `str(a) + str(b)` is larger than `str(b) + str(a)`, through `functools.cmp_to_key`.
