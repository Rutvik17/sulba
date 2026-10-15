A bean's nearest neighbours are the training beans closest to it in the scaled measurements, by straight-line distance. Write `nearest`, which finds them, and `vote`, which names each bean's variety from theirs:

- `nearest` gives, for each bean of `batch`, the rows of `train` of its `k` nearest training beans, nearest first. Two training beans as near as each other come in the order of `train`.
- `vote` gives each bean the variety most of its neighbours have. When varieties tie, the bean takes the variety of the nearest of the tied neighbours.

```
nearest(train, batch, k) -> an array of the rows of train, one row of k for each bean of batch
vote(varieties, neighbours) -> an array of each bean's variety
```

`train` and `batch` are scaled as `scale` gives them, and `varieties` holds each training bean's variety, in the order of `train`.
