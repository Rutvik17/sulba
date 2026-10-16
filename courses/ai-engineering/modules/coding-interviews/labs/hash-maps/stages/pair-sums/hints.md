For each number, the number it needs is `target - number`. Where could you look that up in one step?

---

A dict from each number seen so far to its first position finds the partner in one step. Look it up before adding the current number, so that a number never pairs with itself.
