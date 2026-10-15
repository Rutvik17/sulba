```python
def nearest(train, batch, k):
    rows = []
    for bean in batch:
        distances = ((train - bean) ** 2).sum(axis=1)
        rows.append(np.argsort(distances, kind="stable")[:k])
    return np.array(rows)
```

Squared distances put the training beans in the same order as distances, so the square root is never taken. NumPy's `argsort` sorts with quicksort unless told otherwise, which doesn't keep equal values in their order: with `kind="stable"`, two training beans at the same distance always come in the order of `train`, and the same bean always gets the same neighbours.

```python
def vote(varieties, neighbours):
    chosen = []
    for named in varieties[neighbours]:
        names, counts = np.unique(named, return_counts=True)
        tied = names[counts == counts.max()]
        chosen.append(next(name for name in named if name in tied))
    return np.array(chosen)
```

A tie needs a rule, and the rule changes what the line says. With {% $fig.tie_k %} neighbours, {% $fig.tied %} of the {% $fig.validation %} validation beans have a tied vote. Given to the nearer bean, the vote names {% $fig.nearer %} of the validation beans right; given to the variety that sorts first, as scikit-learn's `KNeighborsClassifier` gives it, {% $fig.first %}. scikit-learn keeps the varieties in sorted order and takes the first with the most votes, so its ties always fall to the same varieties, however far away their beans are.
