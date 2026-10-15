How many neighbours vote changes what the line says. Write `sort_beans`, which names each bean of a batch from its raw measurements, and `choose_k`, which picks how many neighbours vote, on the validation beans of `data/beans.csv`, whose `set` is 1:

- `sort_beans` scales `train` and `batch` by the training beans' statistics, then names each bean of `batch` by its `k` nearest training beans.
- `choose_k` gives the share of the validation beans that each `k` of `ks` names right, in the order of `ks`, and the `k` with the highest share, the smallest if several have it.

```
sort_beans(train, varieties, batch, k) -> an array of each bean's variety
choose_k(train, varieties, validation, validation_varieties, ks) -> (shares, best k)
```

The arrays hold raw measurements, in the columns of `MEASUREMENTS`, and each bean's variety.
