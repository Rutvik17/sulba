Search from each cell, a letter at a time, and mark the cells on the path so far. Is anything worth checking before searching at all?

---

If the word needs more of some letter than the grid has, no path spells it, and `collections.Counter` tells you at once. Then mark a cell, try its four neighbours for the next letter, and unmark it on the way back.
