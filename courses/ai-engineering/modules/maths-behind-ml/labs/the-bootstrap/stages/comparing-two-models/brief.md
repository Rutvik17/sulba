The clinic's second rule calls a sample malignant when its nearest record is malignant. The first rule gets {% $fig.right %} of the {% $fig.new %} new samples right and the second {% $fig.right_b %}, but not the same ones: the two rules disagree on {% $fig.disagree %}. Is either better? A bootstrap answers that too, if both rules' results are resampled together: one resample of the samples, and each rule's accuracy on it.

The clinic will compare its models this way on every sample its partner clinics send, up to {% $fig.million %} at a time. On any resample, the difference between two models' accuracies depends only on how many of its samples model a alone gets right, and how many model b alone does.

Ship `paired_difference`: the percentile interval for model a's accuracy minus model b's, from `repeats` resamples drawn with `rng`, given whether each model is right about each sample.

```
paired_difference(right_a, right_b, confidence, repeats, rng) -> (low, high)
```

It must give the intervals that resampling the samples gives, compare {% $fig.million %} samples with {% $fig.repeats %} resamples in under a second, and refuse results from different samples with a `ValueError`.

There are no hints. The tests are hidden: you see which pass, but not their inputs. Five more checks decide whether it ships.
