```python
def encode(calls, categories):
    columns = [calls[name].to_numpy(dtype=float) for name in NUMBERS]
    for name in CATEGORIES:
        for category in categories[name]:
            columns.append((calls[name] == category).to_numpy(dtype=float))
    return np.column_stack(columns)


def grow(X, said_yes, depth, min_leaf):
    node = {"calls": len(said_yes), "yes": int(said_yes.sum())}
    if depth == 0 or node["yes"] in (0, node["calls"]):
        return node
    best = None
    for column in range(X.shape[1]):
        found = best_split(X[:, column], said_yes, min_leaf)
        if found is not None and (best is None or found[1] < best[2]):
            best = (column, *found)
    if best is None:
        return node
    column, threshold, _ = best
    left = X[:, column] <= threshold
    node["column"], node["threshold"] = column, float(threshold)
    node["left"] = grow(X[left], said_yes[left], depth - 1, min_leaf)
    node["right"] = grow(X[~left], said_yes[~left], depth - 1, min_leaf)
    return node


def score(tree, X):
    shares = []
    for row in X:
        node = tree
        while "column" in node:
            below = row[node["column"]] <= node["threshold"]
            node = node["left"] if below else node["right"]
        shares.append(node["yes"] / node["calls"])
    return np.array(shares)
```

Grown {% $fig.small_depth %} splits deep on the training calls, with at least {% $fig.min_leaf %} calls a leaf, the tree is:

- `pdays` at most {% $fig.root_t %}: {% $fig.left %}
  - `pdays` at most {% $fig.left_t %}: {% $fig.left_left %}
  - `pdays` above {% $fig.left_t %}: {% $fig.left_right %}
- `pdays` above {% $fig.root_t %}: {% $fig.right %}
  - `age` at most {% $fig.right_t %}: {% $fig.right_left %}
  - `age` above {% $fig.right_t %}: {% $fig.right_right %}

Clients the bank had reached lately in an earlier campaign said yes most often, and of the rest, clients over {% $fig.right_t %}. Every call in a leaf gets the same share, so this tree ranks the calls in {% $fig.small_leaves %} groups, and one grown {% $fig.depth %} deep in {% $fig.leaves %}.

A threshold can't compare jobs, so `encode` gives each category a column of 0 and 1, and a split at 0.5 asks whether a call is in that category. The {% $fig.categories %} categories of the {% $fig.category_columns %} category columns make {% $fig.columns %} columns with the {% $fig.numbers %} numbers. Coded instead as 0, 1, 2 and so on in one column, the categories could only be split in runs of their codes, such as the jobs from `admin.` to `housemaid`, which have nothing to do with one another.

`default` says whether a client had defaulted on credit: `no`, `unknown` or `yes`. None of the training calls is `yes`, and the test calls hold {% $fig.default_test %}. That call gets 0 in both of the training calls' `default` columns, so at a split on either category it goes the way of the calls outside it.

scikit-learn tries the columns in an order it draws at random, so where two columns tie, its tree depends on `random_state`. The tests compare trees in which no columns tie.

The tree is greedy: each node takes the best split for its own calls, without looking ahead to the splits below. Finding the tree that does best over every combination of splits is NP-complete, so trees are grown this way, one split at a time.
