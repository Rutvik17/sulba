A tree splits the training calls by the best split of any column, then splits each side the same way, and so on down. Each leaf gives the share of yes among the training calls that reach it, and a new call takes the share of the leaf it reaches.

The tree splits numbers, so a category such as a client's job needs columns of numbers first. Write `encode`, which gives the `NUMBERS` columns as they are, then for each of the `CATEGORIES` columns, a column for each of its categories: 1 for the calls in that category and 0 for the rest. `categories` lists each category column's categories, as the training calls have them:

```python
categories = {name: sorted(train[name].unique()) for name in CATEGORIES}
```

A call in a category the list doesn't have gets 0 in every column of it. Then write `grow` and `score`:

```
encode(calls, categories) -> X, an array with a row for each call
grow(X, said_yes, depth, min_leaf) -> tree
score(tree, X) -> for each row of X, the share of yes in its leaf
```

A tree is a dict. A leaf holds `calls`, the training calls that reach it, and `yes`, how many of them said yes. A node that splits holds those too, and `column`, the index of the column it splits; `threshold`; `left`, the tree grown on the calls at or below the threshold; and `right`, the tree grown on the rest:

```python
{
    "calls": 6,
    "yes": 2,
    "column": 0,
    "threshold": 3.5,
    "left": {"calls": 3, "yes": 0},
    "right": {"calls": 3, "yes": 2},
}
```

A node is a leaf when `depth` is 0, when its calls all said the same, or when no column has a split that keeps `min_leaf` calls on each side. Otherwise it splits by the column whose best split leaves the least impurity, the first such column when columns tie, and grows each side with `depth - 1`. The tests compare the scores with scikit-learn's `DecisionTreeClassifier` with the same `max_depth` and `min_samples_leaf`.
