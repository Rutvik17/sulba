Start `forest.py`. A decision tree grown on the bank's calls depends on the calls it is given: grown on another sample of the same clients, it splits them differently and ranks them differently. A forest grows many trees, each on a sample of its own, and averages their shares of yes.

Each tree's sample is a bootstrap sample: n calls drawn at random from the n training calls, with replacement, so that some calls come twice or more and others not at all. Write `bootstrap`, `grow_forest` and `forest_score`:

```
bootstrap(n, rng) -> n row numbers from 0 to n - 1
grow_forest(X, said_yes, count, rng, min_leaf, max_features) -> (trees, samples)
forest_score(trees, X) -> each row's share of yes, averaged over the trees
```

`rng` is a NumPy random generator, and `bootstrap` returns `rng.integers(0, n, size=n)`. For each tree in turn, `grow_forest` draws its sample with `bootstrap`, then its seed with `int(rng.integers(2**31))`, and fits `DecisionTreeClassifier(min_samples_leaf=min_leaf, max_features=max_features, random_state=seed)` to the sample's rows. A tree's share of yes for each row of `X` is `tree.predict_proba(X)[:, 1]`.

The starter's `encode` gives the calls as the trees read them, a column for each number and each category. The tests compare `forest_score` with scikit-learn's `RandomForestClassifier`, which averages its trees' shares the same way.
