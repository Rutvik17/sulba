The planners can call some patients after discharge, and they'll call the stays the service rates most likely to come back. How many they call is theirs to choose, set by the calls they can make. Each share of the stays sets a probability threshold, and the service calls every stay at or above it.

Add to `model.py`:

```
threshold_for(probabilities, share) -> the probability at or above which lie the share of
    stays with the highest probabilities
calls(y, probabilities, threshold) -> (called, recall, precision) for calling every stay at
    or above threshold
```

`threshold_for` is the probabilities' `1 - share` quantile, as `np.quantile` gives it. From `calls`, `called` is how many stays are called, `recall` is the share of the readmissions among them, and `precision` is the share of them readmitted.

The chart calls the lab's stays by their out-of-fold probabilities from stage 4, which are what the probabilities of new patients will be like. The tests compare your functions with `np.quantile` and with scikit-learn's `recall_score` and `precision_score`.
