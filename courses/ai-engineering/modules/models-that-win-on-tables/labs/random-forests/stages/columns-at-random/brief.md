Trees grown on different samples still look alike. With every column to choose from, {% $fig.every_top_count %} of {% $fig.trees %} trees split the calls first on `pdays`, and the next splits follow from that one. A random forest gives each split only a few columns to choose among, drawn at random for every split. With `max_features="sqrt"`, scikit-learn draws the square root of the number of columns, rounded down: {% $fig.sqrt %} of the {% $fig.columns %}.

Write `auc_by_count`, the AUC of the forest of the first k trees, for each k:

```
auc_by_count(trees, X, said_yes) -> an array of AUCs, for the first 1, 2, ... trees
```

The forest of the first k trees scores each row by the mean of their shares, as `forest_score` does. Import `roc_auc_score` from `sklearn.metrics` at the top of `forest.py`.

The chart grows {% $fig.chart_trees %} trees that choose among every column at each split, and {% $fig.chart_trees %} that choose among columns drawn at random, with the smallest leaf the slider sets, and draws your AUCs for each number of trees.
