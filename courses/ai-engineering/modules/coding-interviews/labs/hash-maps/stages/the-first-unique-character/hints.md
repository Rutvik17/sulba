Whether a character is unique depends on the whole text, so one pass that stops early can't tell yet. What could a first pass gather?

---

Count every character in a first pass, with `collections.Counter`. Then go through the text again and stop at the first character whose count is one.
