You walk along a row of buildings from the first, with `heights[i]` the height of building `i`. Stepping down or level costs nothing. Each step up needs a ladder, or as many bricks as the step is high, and each ladder and brick can be used once. Write `furthest`:

```
furthest(heights, bricks, ladders) -> the index of the furthest building you can reach
```

`furthest([3, 5, 4, 10, 12, 11, 17], 10, 1)` returns 6: the ladder takes one step of 6, and the bricks the others, 2, 2 and 6. With 4 bricks it returns 5. The tests' longest row has {% $fig.buildings %} buildings.
