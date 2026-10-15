A deeper tree splits the calls into smaller groups and fits its training calls more closely with every split. Whether its ranking holds for clients it hasn't seen, the validation calls, whose `set` is 1, tell. Measure a ranking by its AUC, the chance that a call that said yes is scored above one that said no, ties counting half: `roc_auc_score(said_yes, scores)`, which you import at the top of `tree.py` from `sklearn.metrics`.

A node's split depends only on its own calls, not on how deep the tree may grow below it. So a tree grown deep holds every shallower tree: cut at a depth, with each node that deep made a leaf of its `calls` and `yes`, it is the tree grown to that depth. Write `prune`, which returns a tree cut at a depth and leaves the tree it was given as it was. Then write `choose_depth`, which grows one tree to the deepest of `depths` and cuts it at each:

```
prune(tree, depth) -> the tree cut at depth
choose_depth(train, said_yes, validation, validation_yes, depths, min_leaf)
    -> (training AUCs, validation AUCs, best depth)
```

`train` and `validation` are encoded calls, and `depths` lists depths from the smallest up. The AUCs are arrays with one for each depth, and the best depth has the highest validation AUC, the smallest of any tied. The chart draws your AUCs for each depth from 1 to 12, with the smallest leaf the slider sets.
