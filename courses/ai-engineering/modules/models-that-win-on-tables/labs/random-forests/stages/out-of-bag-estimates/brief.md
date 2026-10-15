Each tree's sample leaves out about a third of the training calls: the tree's out-of-bag calls, as new to that tree as the validation calls. Scored only by the trees that left it out, each training call gets a share from trees that never saw it, and the forest an AUC without calls set aside to measure it. Write `out_of_bag`:

```
out_of_bag(trees, samples, X) -> each row's share of yes, averaged over the trees that left it out
```

`samples` holds each tree's sample, the row numbers `grow_forest` drew for it. A row every sample drew has no such tree, and gets `np.nan`. The tests compare `out_of_bag` with the `oob_decision_function_` of scikit-learn's `RandomForestClassifier`, which scores each training row that some tree left out the same way.
