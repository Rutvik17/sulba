`grid` is a list of strings of the same length, its rows of letters, and `word` is a string of at least one letter. Write `traced`:

```
traced(grid, word) -> whether the word can be spelled by moving from cell to cell, up, down,
    left or right, using each cell at most once
```

With the grid `["ABCE", "SFCS", "ADEE"]`, `traced` gives `True` for `"ABCCED"` and `"SEE"`, and `False` for `"ABCB"`, which would use the B twice. The tests' largest grid is {% $fig.side %} by {% $fig.side %}.
