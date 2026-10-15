Start `sampling.py`. The clinic will train its network the way most models are trained: a small batch of records at a time, each step following the gradient on that batch alone. An epoch is one pass through the records. Each epoch shuffles the records into a new order and cuts it into batches, so that every record is used once an epoch and the batches change from one epoch to the next.

Write `shuffled_batches`, one epoch's batches: the row numbers 0 to `n - 1` in a random order drawn from `rng`, cut into batches of `size` rows, the last one smaller when `size` doesn't divide `n`. Then write `batch_mean`, the mean of `values` over a batch's rows.

```
shuffled_batches(n, size, rng) -> a list of arrays of row numbers
batch_mean(values, batch) -> the mean over the batch's rows
```

`rng` is a NumPy generator, made by `np.random.default_rng(seed)`: the same seed gives the same numbers every time. The tests cut the clinic's {% $fig.records %} records into batches of {% $fig.size %}.
