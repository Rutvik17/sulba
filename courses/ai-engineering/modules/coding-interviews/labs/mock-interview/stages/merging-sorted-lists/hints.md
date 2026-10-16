The next number of the merged list is the smallest of the lists' next numbers.

---

Keep each list's next number in a heap, with which list it came from and where. Pop the smallest, then push the number after it from the same list.
