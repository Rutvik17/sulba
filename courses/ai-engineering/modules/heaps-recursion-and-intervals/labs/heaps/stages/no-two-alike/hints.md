Place the letter with the most left first, unless it's the letter you placed last. When does that run out of choices?

---

A max-heap of `(count, letter)` pairs, with `heapq.heapify_max` and `heapq.heappop_max`, gives the letter with the most left. Hold back the letter just placed, and push it back after the next one.
