A model's probabilities become decisions at a threshold: the clinic will send every sample at or above yours for a biopsy.

Add `precision_recall`, which returns the precision and recall of the predictions `p >= threshold`, with precision `0.0` when nothing is predicted positive. Then add `best_threshold`, which returns the highest threshold whose recall is at least `min_recall`: the most cautious cut-off that still finds that share of malignant samples.

```
precision_recall(y, p, threshold=0.5) -> (precision, recall)
best_threshold(y, p, min_recall) -> float
```

The tests call them with the test set's labels and your screener's probabilities for it. If you missed any of stage 4's problems, this stage starts from the fixed screener. There are no hints. The tests are hidden: you see which pass, but not their inputs. Two more checks decide whether it ships.
