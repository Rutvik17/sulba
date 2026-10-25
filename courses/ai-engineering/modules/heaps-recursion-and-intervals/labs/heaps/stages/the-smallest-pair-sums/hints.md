The smallest pair is the two firsts. Once a pair `(first[i], second[j])` is taken, which pairs could come next?

---

Start a heap with `(first[i] + second[0], i, 0)` for the first k places of `first`. Each pair taken adds the pair after it in its row, `j + 1`, and sums, then places, decide the order.
