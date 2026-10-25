`points` is a list of at least two points `(x, y)` with whole-number coordinates. Write `closest`:

```
closest(points) -> the smallest squared distance between two of the points
```

The squared distance between `(x1, y1)` and `(x2, y2)` is `(x1 - x2) ** 2 + (y1 - y2) ** 2`. `closest([(0, 0), (5, 5), (1, 1), (9, 0)])` returns 2. Two points can be the same, at a distance of 0. The tests' longest list has {% $fig.points %} points.
