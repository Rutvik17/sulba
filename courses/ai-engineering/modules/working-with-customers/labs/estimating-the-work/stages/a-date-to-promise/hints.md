Sort the finishes. Which place in the sorted list has at least the share `chance` of the runs at or before it?

---

With `n` runs, it's place `ceil(chance * n)`, counting from 1. `chance_by` counts the finishes that are `<= day`.
