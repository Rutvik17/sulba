`re.findall(r"\w+", text.lower())` gives the runs of letters, digits and underscores.

---

Count each passage's words with `collections.Counter`, and keep, for each word, the rows that hold it and how many times each does. A question then reads only the passages that hold its words.

---

`$k_1 (1 - b + b \lvert p \rvert / m)$` is the same for every word of a passage: work it out for every passage at once, as a NumPy array, in `__init__`. `np.argsort(-scores, kind="stable")` gives the rows from the highest score, keeping tied rows in their order.
