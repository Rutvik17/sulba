Before the call centre works from the tree's list, its managers want to read the tree: one rule for each leaf, saying which clients reach it and how many of its training calls said yes. Write `rules`:

```
rules(tree, columns) -> a list of rules, the likeliest first
```

`columns` names each column of the array the tree was grown on: a number column by its name, such as `"age"`, and a category's column by a pair, such as `("job", "admin.")`. For an array from `encode`:

```python
columns = NUMBERS + [(name, c) for name in CATEGORIES for c in categories[name]]
```

A rule is a dict with the leaf's `calls` and `yes`, and `conditions`: for each column the path from the root to the leaf splits on, one condition that holds all of its splits on that column.

- A number column's condition is a pair `(low, high)`, for the calls with `low < value <= high`. A side with no bound is `-np.inf` or `np.inf`.
- A category column's condition is `("is", category)` once the path has gone right on one of its categories, and otherwise `("is not", [...])`, the categories it went left on, sorted.

A path that goes left on `age` at 60.5, then right on `age` at 30.5, then left on `("job", "admin.")`, gives:

```python
{"age": (30.5, 60.5), "job": ("is not", ["admin."])}
```

List the rules from the highest share of yes to the lowest, with equal shares in the tree's order, from left to right. Hidden tests and checks then try the rules on the bank's calls.
