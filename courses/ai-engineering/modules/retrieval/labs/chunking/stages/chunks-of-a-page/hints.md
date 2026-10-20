`re.finditer(r"\S+", text)` finds each word, and a match's `span()` gives its first character and the one after its last.

---

`range(0, len(places), size - overlap)` gives each window's first word. Stop once a window reaches the last word, or a window that shares words would come after it.

---

`re.finditer(r"[^\n]+(?:\n(?!\n)[^\n]+)*", text)` finds each block: lines joined by a single newline. Keep the words a chunk holds so far, and start a new chunk when the next block would take it past `most`.
