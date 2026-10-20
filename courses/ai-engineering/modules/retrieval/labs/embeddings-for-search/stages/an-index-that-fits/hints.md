`np.savez(file, ids=..., codes=..., low=..., high=...)` writes several arrays to one file, and `np.load(path)` reads them back by name. An array of strings, `np.array(ids)`, takes 4 bytes for each character of its longest id.

---

A vector's bytes are its numbers times the bytes of each: 256 numbers of a byte each take 256, and 64 float32 numbers take 256 too. Shorter vectors gives the hit rate of each on the validation questions.

---

Shorten the questions to as many numbers as the passages, and score them against `restore(...)` of the codes, which you can work out once when the index is built or loaded.
