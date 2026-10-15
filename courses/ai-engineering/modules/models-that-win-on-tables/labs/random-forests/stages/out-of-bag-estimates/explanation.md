```python
def out_of_bag(trees, samples, X):
    total, count = np.zeros(len(X)), np.zeros(len(X))
    for tree, sample in zip(trees, samples, strict=True):
        left_out = np.ones(len(X), dtype=bool)
        left_out[sample] = False
        if left_out.any():
            total[left_out] += tree.predict_proba(X[left_out])[:, 1]
            count[left_out] += 1
    shares = np.full(len(X), np.nan)
    np.divide(total, count, out=shares, where=count > 0)
    return shares
```

A forest of {% $fig.trees %} trees with columns drawn at random and at least {% $fig.min_leaf %} calls a leaf ranks its training calls, scored out of bag, at {% $fig.oob %}, and the validation calls at {% $fig.validation %}. Scored by every tree, its own training calls rank at {% $fig.in_sample %}: each tree has seen most of them, and remembers them.

A call is missed by one sample with a chance of about `$1/e$`, so with a few trees, many calls have no tree that left them out:

| Trees | Training calls every sample drew |
| --- | --- |
| {% $fig.few_0 %} | {% $fig.never_0 %} |
| {% $fig.few_1 %} | {% $fig.never_1 %} |
| {% $fig.few_2 %} | {% $fig.never_2 %} |
| {% $fig.few_3 %} | {% $fig.never_3 %} |

Each call's out-of-bag share comes from about a third of the trees, the share of a smaller forest than the one that scores new calls. With few trees, the estimate can run below the forest it estimates: grown {% $fig.small %} trees, the forest ranks its training calls out of bag at {% $fig.small_oob %} and the validation calls at {% $fig.small_validation %}.

scikit-learn gives a row that no tree left out a share of 0, with a warning that some rows have no out-of-bag score. `np.nan` says plainly that there is no estimate, and the AUC is taken over the rows that have one.
