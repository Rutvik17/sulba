The clinic will train on {% $fig.workers %} workers at once, each a process with its own machine or GPU. At each step, every worker works out the gradient on its own batch, the workers average their gradients, and all take the same step. So each worker needs its own share of every epoch's records, and as many batches as every other worker, to take every step together.

Ship `worker_batches`, the batches that the worker numbered `rank`, from 0 to `workers - 1`, trains on in an epoch:

- All the workers share one order of the records for each epoch, which depends only on `seed` and `epoch`: a new order for every seed and epoch, and the same order each time the same pair is asked for.
- Worker `rank` takes the records at positions `rank`, `rank + workers`, `rank + 2 * workers` and so on of that order, cut into batches of `size` rows, the last one smaller.
- When `workers` doesn't divide `n`, the order carries on from its start until it does, so that every worker gets the same number of records, as PyTorch's `DistributedSampler` does.

```
worker_batches(n, size, workers, rank, epoch, seed) -> a list of arrays of row numbers
```

There are no hints. The tests are hidden: you see which pass, but not their inputs. Four more checks decide whether it ships.
