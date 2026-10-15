The records are {% $fig.share %} malignant, so a batch of {% $fig.size %} holds {% $fig.plain %} malignant records on average. When one class is rare, many batches hold none of its records, and training often draws records with weights instead: PyTorch's `WeightedRandomSampler` draws row numbers, by default with replacement, each with a probability in proportion to its weight.

Write `weighted_choice`, `size` row numbers drawn with replacement, row `$i$` with probability `$w_i / \sum_j w_j$`. Take one uniform number for each draw from `rng.random(size)`, scale it by the weights' total, and take the first row whose running total of weights is above it.

Then write `balanced_weights`: for each record, 1 over the number of records with its label, so that every class has the same total weight.

A batch drawn with weights doesn't stand for the records as they are. Write `reweighted_mean`, which estimates the mean of `values` over all `$n$` records from such a batch by counting each row's value `$v_i$` as `$v_i / (n p_i)$`, where `$p_i$` is the row's probability.

```
weighted_choice(weights, size, rng) -> an array of size row numbers
balanced_weights(labels) -> an array with a weight for each record
reweighted_mean(values, batch, weights) -> a number
```

The tests compare your draws with NumPy's `Generator.choice`, given the same seed and the probabilities.
