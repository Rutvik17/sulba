Each row holds exactly one queen. Placing them row by row, what do you need to know to tell whether a square is attacked?

---

Keep sets of the columns, the rising diagonals, `row + column`, and the falling diagonals, `row - column`, already taken. Place a queen, count the ways for the rows below, and take it back.
