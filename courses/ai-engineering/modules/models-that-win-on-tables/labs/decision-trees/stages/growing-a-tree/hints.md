`(calls[name] == category).to_numpy(dtype=float)` is one category's column, and `np.column_stack` puts a list of columns side by side.

---

`grow` calls itself. Once a node has its best split, `left = X[:, column] <= threshold` picks the rows on each side, and `grow(X[left], said_yes[left], depth - 1, min_leaf)` grows the left side.

---

To score a row, start at the root and step to `node["left"]` or `node["right"]` until the node has no `"column"`. Its share is `node["yes"] / node["calls"]`.
