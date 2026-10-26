Only the k largest numbers so far can be the answer, now or later. Which of them is the answer, and which goes when a larger number comes?

---

A min-heap of the k largest keeps the kth largest at index 0. A new number joins only if it's larger than that, and `heapreplace` swaps it in.
