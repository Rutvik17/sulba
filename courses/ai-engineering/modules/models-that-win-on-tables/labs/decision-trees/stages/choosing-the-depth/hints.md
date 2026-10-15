`prune` follows the same shape as `grow`: a leaf when `depth` is 0 or the node has no `"column"`, and otherwise a copy of the node whose `left` and `right` are cut at `depth - 1`. `{**node, "left": ..., "right": ...}` copies a dict with two of its keys replaced.

---

`grow(train, said_yes, max(depths), min_leaf)` once. Then for each depth, `score(prune(tree, depth), train)` gives the scores to pass to `roc_auc_score` with `said_yes`, and the same on `validation` with `validation_yes`.

---

`np.argmax` returns the first of tied maxima, so `depths[int(np.argmax(validated))]` is the smallest best depth.
