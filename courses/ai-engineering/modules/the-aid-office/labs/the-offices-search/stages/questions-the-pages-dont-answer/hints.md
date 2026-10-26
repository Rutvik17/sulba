`SELECT 1 - min(embedding <=> %s) FROM passages` reads every passage, which for the office's passages is quick, and exact.

---

Sort the similarities highest first. The threshold is the first whose count so far, over them all, reaches `keep`: compare `count / len(similarities) >= keep`, rather than working out the place from `keep * len(similarities)`, whose float can land just above a whole number.
