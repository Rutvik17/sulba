Build what the search needs once: each passage's word counts, and for each word, the passages that hold it. Then a question only looks at the passages that share a word with it.

---

BM25 scores a passage by each word it shares with the question, weighted by how few passages hold the word. Each repeat of a word in a passage adds less than the one before, and a long passage's words count for less.
