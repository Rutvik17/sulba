Write `spiral`, which reads a grid's values in a spiral:

```
spiral(grid) -> every value, clockwise from the top left corner, ring by ring inwards
```

`grid` is a list of rows of the same length. Read the top row left to right, down the right column, the bottom row right to left and up the left column, then the next ring in the same way, until every value is read once:

```python
grid = [
    ["a", "b", "c"],
    ["d", "e", "f"],
    ["g", "h", "i"],
    ["j", "k", "l"],
]
spiral(grid)
# ["a", "b", "c", "f", "i", "l", "k", "j", "g", "d", "e", "h"]
```

A grid can have one row or one column, and an empty grid, `[]`, gives `[]`.
