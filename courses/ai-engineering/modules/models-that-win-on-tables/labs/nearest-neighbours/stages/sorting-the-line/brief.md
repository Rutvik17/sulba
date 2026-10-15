The line runs all day, and not everything on it is a bean it can name: a stone, or a bean halfway between two varieties. Write `Line`, which is set up once from the training beans and then sorts every batch that comes down the line, saying when it can't name a bean:

- A bean is `UNKNOWN` when its nearest training bean is farther from it than any training bean is from its own nearest other training bean: farther than the training beans' reach.
- A bean within reach is `UNSURE` when no variety has more than half of its `k` neighbours' votes, so that a person looks at it.
- Every other bean is named by the variety with most votes.

```
Line(train, varieties, k)
line.sort(batch) -> an array of each bean's variety, UNKNOWN or UNSURE
```

The line keeps the training beans' statistics and their reach from when it is set up, for every batch after.
