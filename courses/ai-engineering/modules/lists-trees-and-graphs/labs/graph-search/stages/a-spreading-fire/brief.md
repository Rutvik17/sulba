A forest's map is a list of rows, each a string of the same length: `T` for a tree, `F` for a tree on fire, and `.` for open ground. Each minute, every tree on fire sets alight the trees next to it, above, below, left and right. Write `minutes_to_burn`:

```
minutes_to_burn(rows) -> the minutes until every tree is on fire, or -1 if some tree never
    catches
```

This forest has burnt through after 5 minutes:

```
F.TT
TTT.
.T.F
```

A forest with no tree that isn't already on fire takes 0 minutes. Open ground never burns, so a tree cut off by it never catches. The tests' largest forest is {% $fig.side %} squares a side, and its fire takes {% $fig.minutes %} minutes to reach the last tree.
