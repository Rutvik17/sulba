Read the text from its start the way the schema reads: `{`, then each key in quotes with its colon and its value, a comma between them, then `}`. A function that reads one value from a position and says where it ends, or that the text stopped partway through it, or that it can't be valid, does most of the work, and calls itself for an object's values.

---

For an `enum`, compare the text from that position with each string as JSON writes it, quotes included: the text starts with one, or stops partway through one, or neither. Digits end at the first character that isn't one, and when the text stops in them, the question is whether any allowed number starts with them.

---

`mask` asks `allowed` once for each token. In `generate`, `max` over the indexes the mask allows, with `key=` their scores, gives the first of the highest.
