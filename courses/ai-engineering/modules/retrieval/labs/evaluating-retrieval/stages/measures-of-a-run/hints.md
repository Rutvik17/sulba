`shown[:k]` is the first `k` passages, or every passage if fewer are shown.

---

The best ranking puts `min(k, len(relevant))` relevant passages first, so its DCG is the sum of `1 / math.log2(i + 1)` for `i` from 1 to that number.

---

`run.get(question, [])` gives the passages a run shows for a question, or none.
