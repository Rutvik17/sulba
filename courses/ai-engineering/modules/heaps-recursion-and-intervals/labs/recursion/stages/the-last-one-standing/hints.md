Once the first person leaves, the rest is the same problem, one person smaller, counted from the next person. How does the answer for `people - 1` give the answer for `people`?

---

Counting places from 0, the survivor of a circle of 1 is at place 0, and a circle of `n` puts it `step` places further on than a circle of `n - 1`: `(place + step) % n`. Work it out from 2 up to `people` in a loop, since a function calling itself would go a call deep per person.
