Build each string a bracket at a time. When can you add a `(`, and when a `)`?

---

Add `(` while fewer than `pairs` are open, and `)` while fewer have closed than opened. A string with `pairs` closed is finished, and trying `(` before `)` keeps the list sorted.
