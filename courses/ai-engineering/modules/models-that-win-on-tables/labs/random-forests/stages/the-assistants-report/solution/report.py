"""The forest's report to the bank: the AUC to expect, and how much its ranking leans on each
column."""

import numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.tree import DecisionTreeClassifier

NUMBERS = ["age", "campaign", "pdays", "previous"]
CATEGORIES = [
    "job",
    "marital",
    "education",
    "default",
    "housing",
    "loan",
    "contact",
    "poutcome",
]
# The forest's trees, their smallest leaf and the columns each split may choose from, and
# the seed that makes the report the same each time it runs.
TREES, MIN_LEAF, MAX_FEATURES, SEED = 15, 10, "sqrt", 0


def encode(calls, categories):
    """The calls as an array: the numbers, then a column of 0 and 1 for each category."""
    columns = [calls[name].to_numpy(dtype=float) for name in NUMBERS]
    for name in CATEGORIES:
        for category in categories[name]:
            columns.append((calls[name] == category).to_numpy(dtype=float))
    return np.column_stack(columns)


def grow(X, said_yes, count, rng):
    """count trees, each on its own bootstrap sample, and the samples."""
    trees, samples = [], []
    for _ in range(count):
        sample = rng.integers(0, len(X), size=len(X))
        tree = DecisionTreeClassifier(
            min_samples_leaf=MIN_LEAF,
            max_features=MAX_FEATURES,
            random_state=int(rng.integers(2**31)),
        )
        trees.append(tree.fit(X[sample], said_yes[sample]))
        samples.append(sample)
    return trees, samples


def score(trees, X):
    """Each row's share of yes, averaged over the trees."""
    return np.mean([tree.predict_proba(X)[:, 1] for tree in trees], axis=0)


def expected_auc(trees, samples, X, said_yes):
    """The forest's AUC on calls it hasn't seen, estimated from the training calls each tree
    left out."""
    total, count = np.zeros(len(X)), np.zeros(len(X))
    for tree, sample in zip(trees, samples, strict=True):
        left_out = np.ones(len(X), dtype=bool)
        left_out[sample] = False
        total[left_out] += tree.predict_proba(X[left_out])[:, 1]
        count[left_out] += 1
    scored = count > 0
    return roc_auc_score(said_yes[scored], total[scored] / count[scored])


def importance(trees, calls, categories, rng):
    """For each column, how far the AUC on calls falls when its values are shuffled."""
    said_yes = (calls["subscribed"] == "yes").to_numpy()
    base = roc_auc_score(said_yes, score(trees, encode(calls, categories)))
    falls = {}
    for name in NUMBERS + CATEGORIES:
        shuffled = calls.copy()
        shuffled[name] = rng.permutation(calls[name].to_numpy())
        auc = roc_auc_score(said_yes, score(trees, encode(shuffled, categories)))
        falls[name] = base - auc
    return falls


def report(trees, samples, train, validation, rng):
    """The AUC to expect, and each column's importance on the validation calls."""
    categories = {name: sorted(train[name].unique()) for name in CATEGORIES}
    X, said_yes = encode(train, categories), (train["subscribed"] == "yes").to_numpy()
    auc = expected_auc(trees, samples, X, said_yes)
    return auc, importance(trees, validation, categories, rng)


def run(train, validation):
    """The forest grown on the training calls, and its report."""
    rng = np.random.default_rng(SEED)
    categories = {name: sorted(train[name].unique()) for name in CATEGORIES}
    X, said_yes = encode(train, categories), (train["subscribed"] == "yes").to_numpy()
    trees, samples = grow(X, said_yes, TREES, rng)
    return report(trees, samples, train, validation, rng)
