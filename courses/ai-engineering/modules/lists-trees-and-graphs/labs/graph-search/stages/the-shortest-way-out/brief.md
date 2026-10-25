A maze is a list of rows, each a string of the same length: `#` for a wall, `.` for an open square, one `S` for the start and one `E` for the exit. A step moves to the open square above, below, left or right. Write `shortest_way`:

```
shortest_way(rows) -> the fewest steps from S to E, or -1 if no way leads there
```

In this maze the shortest way out takes 9 steps:

```
S.#.....
.##.###.
....#E..
.##.....
```

The tests' longest maze is {% $fig.side %} squares a side, and its only way out is {% $fig.steps %} steps long. Another is an open room {% $fig.room %} squares a side, with the start and the exit in opposite corners.
