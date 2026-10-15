import numpy as np
import pandas as pd
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
# The assistant's forest and its seed, the seed of the explanation's shuffles, and the seeds of
# three runs that each start from a seed of their own.
TREES, MIN_LEAF, SEED, SHUFFLES = 15, 10, 0, 1
RUNS = [1, 2, 3]


def encode(calls, categories):
    columns = [calls[name].to_numpy(dtype=float) for name in NUMBERS]
    for name in CATEGORIES:
        for category in categories[name]:
            columns.append((calls[name] == category).to_numpy(dtype=float))
    return np.column_stack(columns)


def grow(X, said_yes, rng):
    trees, samples = [], []
    for _ in range(TREES):
        sample = rng.integers(0, len(X), size=len(X))
        tree = DecisionTreeClassifier(
            min_samples_leaf=MIN_LEAF,
            max_features="sqrt",
            random_state=int(rng.integers(2**31)),
        )
        trees.append(tree.fit(X[sample], said_yes[sample]))
        samples.append(sample)
    return trees, samples


def score(trees, X):
    return np.mean([tree.predict_proba(X)[:, 1] for tree in trees], axis=0)


def importance(trees, calls, categories, rng):
    said_yes = (calls["subscribed"] == "yes").to_numpy()
    base = roc_auc_score(said_yes, score(trees, encode(calls, categories)))
    falls = {}
    for name in NUMBERS + CATEGORIES:
        shuffled = calls.copy()
        shuffled[name] = rng.permutation(calls[name].to_numpy())
        falls[name] = base - roc_auc_score(
            said_yes, score(trees, encode(shuffled, categories))
        )
    return falls


def figures():
    table = pd.read_csv("data/calls.csv")
    train, validation = table[table["set"] == 0], table[table["set"] == 1]
    categories = {name: sorted(train[name].unique()) for name in CATEGORIES}
    X, V = encode(train, categories), encode(validation, categories)
    said_yes = (train["subscribed"] == "yes").to_numpy()
    validation_yes = (validation["subscribed"] == "yes").to_numpy()
    trees, samples = grow(X, said_yes, np.random.default_rng(SEED))
    one, _ = grow(X, said_yes, np.random.default_rng(SEED))
    total, count = np.zeros(len(X)), np.zeros(len(X))
    for tree, sample in zip(trees, samples, strict=True):
        left_out = np.ones(len(X), dtype=bool)
        left_out[sample] = False
        total[left_out] += tree.predict_proba(X[left_out])[:, 1]
        count[left_out] += 1
    scored = count > 0
    on_train = importance(trees, train, categories, np.random.default_rng(SHUFFLES))
    on_validation = importance(
        trees, validation, categories, np.random.default_rng(SHUFFLES)
    )
    ranked = sorted(on_train, key=lambda name: -on_train[name])
    # The cost names the column the training calls rank third.
    assert ranked[2] == "education"
    found = {
        "trees": str(TREES),
        "one": f"{roc_auc_score(validation_yes, score(one[:1], V)):.3f}",
        "forest": f"{roc_auc_score(validation_yes, score(trees, V)):.3f}",
        "in_sample": f"{roc_auc_score(said_yes, score(trees, X)):.3f}",
        "oob": f"{roc_auc_score(said_yes[scored], total[scored] / count[scored]):.3f}",
    }
    for name in ["education", "marital"]:
        # The cost says neither makes a difference on the validation calls.
        assert on_validation[name] <= 0
        found[f"{name}_train"] = f"{on_train[name]:.3f}"
        found[f"{name}_validation"] = f"{on_validation[name]:.3f}".replace("-", "−")
    for i, seed in enumerate(RUNS):
        rng = np.random.default_rng(seed)
        run_trees, _ = grow(X, said_yes, rng)
        falls = importance(run_trees, validation, categories, rng)
        assert max(falls, key=falls.get) == "contact"
        found[f"contact_{i}"] = f"{falls['contact']:.3f}"
    return found
