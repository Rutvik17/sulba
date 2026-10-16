Sorting works, in time in proportion to `$n \log n$`. Can you keep just the `k` largest seen so far, cheaply?

---

Keep the `k` largest in a min-heap with `heapq`: a number larger than the heap's smallest replaces it. At the end, the heap's smallest is the answer.
