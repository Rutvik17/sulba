A sudoku is a 9 by 9 grid in which each row, each column and each of the nine 3 by 3 boxes holds the digits 1 to 9 once each. A puzzle gives some of the digits, its clues, and has one way to fill the rest. Write `solved`:

```
solved(grid) -> the puzzle's grid with every empty cell filled
```

`grid` is 9 strings of 9 characters, its rows, with `.` for an empty cell, and `solved` returns the filled grid in the same form. The first rows of the tests' first puzzle are `"..4....5."`, `"..3....48"` and `"....63..."`. The tests' hardest puzzles give as few as {% $fig.fewest %} clues.
