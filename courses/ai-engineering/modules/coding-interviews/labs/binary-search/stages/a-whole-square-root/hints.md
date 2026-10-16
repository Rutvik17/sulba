The answer is somewhere from `0` to `n`, and a number's square says whether the answer is above or below it.

---

Binary search for the largest `r` with `r * r <= n`. To make the bounds meet, round the middle up: `(low + high + 1) // 2`.
