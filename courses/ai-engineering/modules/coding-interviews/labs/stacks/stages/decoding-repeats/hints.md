At each `[`, what has been built so far has to wait while the part inside is built.

---

At `[`, push the text built so far and the count, then start the part afresh. At `]`, pop them and add the part, repeated count times, to the text that waited.
