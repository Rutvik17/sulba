`range(start, end)` gives each character of a part. A character is held when a chunk on the same page has `start <= at < end`.

---

Precision divides by every found chunk's `end - start` added up, so a character two chunks hold counts twice there, and once in what they hold of the answer.

---

A chunk holds part of the answer when they're on the same page, the chunk starts before the part ends, and it ends after the part starts.
