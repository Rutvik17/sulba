```python
def bootstrap(n, rng):
    return rng.integers(0, n, size=n)


def grow_forest(X, said_yes, count, rng, min_leaf, max_features):
    trees, samples = [], []
    for _ in range(count):
        sample = bootstrap(len(X), rng)
        seed = int(rng.integers(2**31))
        tree = DecisionTreeClassifier(
            min_samples_leaf=min_leaf, max_features=max_features, random_state=seed
        )
        trees.append(tree.fit(X[sample], said_yes[sample]))
        samples.append(sample)
    return trees, samples


def forest_score(trees, X):
    return np.mean([tree.predict_proba(X)[:, 1] for tree in trees], axis=0)
```

Each draw misses a given call with a chance of `$1 - 1/n$`, so a sample of n draws misses it with a chance of `$(1 - 1/n)^n$`, which comes close to `$1/e$` as n grows. A bootstrap sample of the {% $fig.train %} training calls holds {% $fig.distinct %} of them on average, near `$1 - 1/e$`, {% $fig.limit %}.

Grown until no leaf can be split, {% $fig.trees %} trees on {% $fig.trees %} samples rank the validation calls with AUCs from {% $fig.tree_low %} to {% $fig.tree_high %}, {% $fig.tree_mean %} on average. Averaged, the same trees rank them at {% $fig.forest %}. Each tree fits the chance details of its own sample, a different few in each, and the average keeps more of what the samples have in common than of what each has alone. Growing models on bootstrap samples and averaging them is called bagging.
