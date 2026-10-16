A row of bars stands side by side, each one wide, the bar at position `i` of height `heights[i]`. Rain fills the gaps between them, and water above a bar rises to the lower of the highest bar on its left and the highest on its right, so it spills off both ends. Write `trapped_water`:

```
trapped_water(heights) -> how much water the bars hold after the rain
```

`trapped_water([3, 0, 2, 0, 4, 1, 2])` returns `8`: `3` above each `0`, `1` above the `2` between them, and `1` above the `1`. The tests' longest row has {% $fig.bars %} bars.
