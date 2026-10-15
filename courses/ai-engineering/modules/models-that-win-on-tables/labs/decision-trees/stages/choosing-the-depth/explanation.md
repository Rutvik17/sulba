```python
def prune(tree, depth):
    if depth == 0 or "column" not in tree:
        return {"calls": tree["calls"], "yes": tree["yes"]}
    return {
        **tree,
        "left": prune(tree["left"], depth - 1),
        "right": prune(tree["right"], depth - 1),
    }


def choose_depth(train, said_yes, validation, validation_yes, depths, min_leaf):
    tree = grow(train, said_yes, max(depths), min_leaf)
    trained, validated = [], []
    for depth in depths:
        cut = prune(tree, depth)
        trained.append(roc_auc_score(said_yes, score(cut, train)))
        validated.append(roc_auc_score(validation_yes, score(cut, validation)))
    return np.array(trained), np.array(validated), depths[int(np.argmax(validated))]
```

With at least {% $fig.min_leaf %} calls a leaf, the validation AUC is highest at depth {% $fig.best %}, {% $fig.best_validation %}. The training AUC climbs with every split, from {% $fig.best_training %} at depth {% $fig.best %} to {% $fig.deep_training %} at depth {% $fig.deepest %}, while the validation AUC falls to {% $fig.deep_validation %}. The deeper splits are each chosen on fewer calls, and past depth {% $fig.best %} they fit what happened to be true of those calls more than what holds for other clients. A tree's AUC on its own training calls never falls as it deepens, so it can't choose the depth.

The smallest leaf limits the tree too. With leaves of {% $fig.one %} call, the training AUC reaches {% $fig.one_training %} at depth {% $fig.deepest %} and the validation AUC falls to {% $fig.one_validation %}. With at least {% $fig.big_leaf %} calls a leaf, the validation AUC peaks at {% $fig.big_validation %}, at depth {% $fig.big_best %}, above the {% $fig.best_validation %} of leaves of {% $fig.min_leaf %}. The test calls, though, score the two trees {% $fig.big_test %} and {% $fig.test %}: the gap on the validation calls doesn't hold on calls neither choice saw. Each choice made on the validation calls takes the best of several tries on the same calls, so the winner's validation AUC flatters it, and the more tries, the more it does.
