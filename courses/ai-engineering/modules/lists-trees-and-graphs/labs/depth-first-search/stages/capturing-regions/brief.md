`board` is a list of strings of `X` and `O`, its rows, all the same length. A region is a group of `O`s joined up, down, left or right. Write `captured`:

```
captured(board) -> the board with every region that doesn't touch the edge turned to Xs
```

`captured(["XXXX", "XOOX", "XXOX", "XOXX"])` returns `["XXXX", "XXXX", "XXXX", "XOXX"]`: the region in the middle is captured, and the `O` on the bottom edge stays. The tests' largest board is {% $fig.side %} by {% $fig.side %}.
