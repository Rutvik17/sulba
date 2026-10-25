Answer the queries in sorted order, not the order given. As the query grows, which intervals become possible, and which can never be used again?

---

Sort the intervals by left end. For each query in sorted order, push every interval that starts by it onto a heap of `(size, right)`, then pop the top while its right end is before the query. The top is then the answer.
