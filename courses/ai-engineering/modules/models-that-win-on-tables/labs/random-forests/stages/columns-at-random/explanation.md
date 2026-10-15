```python
def auc_by_count(trees, X, said_yes):
    shares = np.array([tree.predict_proba(X)[:, 1] for tree in trees])
    averages = np.cumsum(shares, axis=0) / np.arange(1, len(trees) + 1)[:, None]
    return np.array([roc_auc_score(said_yes, average) for average in averages])
```

With at least {% $fig.min_leaf %} calls a leaf and {% $fig.trees %} trees:

| Each split chooses among | Columns split first | Trees ranked alone, mean AUC | The forest's AUC |
| --- | --- | --- | --- |
| Every column | {% $fig.every_roots %} | {% $fig.every_tree %} | {% $fig.every_forest %} |
| {% $fig.sqrt %} columns drawn at random | {% $fig.random_roots %} | {% $fig.random_tree %} | {% $fig.random_forest %} |

With columns drawn at random, the first splits spread over {% $fig.random_roots %} columns, and the most common, on `previous`, starts only {% $fig.random_top_count %} of the trees. The trees differ more from one another, and ranked alone, they do no worse on average than the bagged trees. Averaged, they rank the validation calls better than the bagged trees that nearly all start from `pdays`.

Fewer columns at each split make the trees differ more, which the average gains from, but give each split less to choose from, so each tree fits its training calls less closely. More trees make the forest's shares steadier, up to a number of trees beyond which more add little, while each tree still costs time to grow and to score.
