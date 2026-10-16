A row of upright lines stands one step apart, the line at position `i` of height `heights[i]`. Two lines and the ground hold water up to the lower line, so lines `i` and `j` hold `min(heights[i], heights[j]) * (j - i)`. Write `most_water`:

```
most_water(heights) -> the most water two of the lines can hold
```

`most_water([2, 7, 3, 6, 4, 8, 1])` returns `28`, from the lines of heights `7` and `8`, four steps apart. Fewer than two lines hold nothing, so they give `0`.

The tests' longest row has {% $fig.lines %} lines.
