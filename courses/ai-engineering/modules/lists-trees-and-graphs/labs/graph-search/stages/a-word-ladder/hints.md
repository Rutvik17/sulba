Think of each word as a node, linked to the words one letter away. The shortest ladder is then the shortest path from `start` to `end`. Which search finds that?

---

Comparing every word with every other to find the links is slow for a long list. Instead, file each word under the patterns it fits with one letter blanked out, such as `c*ld` for `cold`: two words are a letter apart when they share a pattern.

---

Search breadth first from `start`, counting words as you go. When you've followed a pattern's words once, you never need it again.
