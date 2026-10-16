Comparing every word with every other is slow. What could anagrams share, so that each word finds its group in one step?

---

Anagrams have the same letters in sorted order. A dict from those sorted letters to a list of words gathers each group, and a dict keeps its keys in the order they were added.
