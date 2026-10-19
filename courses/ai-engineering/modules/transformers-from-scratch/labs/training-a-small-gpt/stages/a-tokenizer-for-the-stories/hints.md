Split the stories into pieces once and count them: `Counter(piece for story in stories for piece in PATTERN.findall(story))`. Then work on each distinct piece's bytes, `list(piece.encode())`, with its count as its weight.

---

`min(pairs, key=lambda pair: (-pairs[pair], pair))` picks the pair seen most often, and of those seen as often, the pair whose numbers come first.

---

Counting every pair again after each merge works, but most merges change only a few pieces. Keep each pair's count, and the pieces it's in: when a merge changes a piece, take its old pairs away from the counts and add its new ones.

---

In `encode`, split the text on `END` first, so no story's piece holds a separator. Many pieces repeat, so keep each piece's tokens the first time you work them out.
