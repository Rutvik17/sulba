A map is a list of rows, each a string of the same length: `#` for a square of land and `.` for one of water. Land squares that touch along an edge, above, below, left or right, are on the same island; squares that touch only at a corner aren't. Write `islands`:

```
islands(rows) -> the number of islands on the map
```

This map has 5 islands:

```
##..#
#...#
..#..
.....
##.##
```

A map with no rows, or no land, has none. The tests' largest map is {% $fig.side %} squares a side, and its one island winds through {% $fig.cells %} of them.
