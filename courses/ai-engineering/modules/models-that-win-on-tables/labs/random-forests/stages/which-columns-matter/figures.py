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
PAST = ["pdays", "previous", "poutcome"]
# The forest the explanation measures, its shuffles, and the shuffles the checks make.
TREES, MIN_LEAF, SEED, REPEATS, SHUFFLES, CHECK_REPEATS = 50, 10, 0, 5, 1, 2


def encode(calls, categories):
    columns = [calls[name].to_numpy(dtype=float) for name in NUMBERS]
    for name in CATEGORIES:
        for category in categories[name]:
            columns.append((calls[name] == category).to_numpy(dtype=float))
    return np.column_stack(columns)


def figures():
    table = pd.read_csv("data/calls.csv")
    train, validation = table[table["set"] == 0], table[table["set"] == 1]
    categories = {name: sorted(train[name].unique()) for name in CATEGORIES}
    X, said_yes = encode(train, categories), (train["subscribed"] == "yes").to_numpy()
    validation_yes = (validation["subscribed"] == "yes").to_numpy()
    rng = np.random.default_rng(SEED)
    trees = []
    for _ in range(TREES):
        sample = rng.integers(0, len(X), size=len(X))
        tree = DecisionTreeClassifier(
            min_samples_leaf=MIN_LEAF,
            max_features="sqrt",
            random_state=int(rng.integers(2**31)),
        )
        trees.append(tree.fit(X[sample], said_yes[sample]))

    def score(calls):
        coded = encode(calls, categories)
        return np.mean([tree.predict_proba(coded)[:, 1] for tree in trees], axis=0)

    groups = {name: [name] for name in NUMBERS + CATEGORIES}
    groups |= {"past": PAST, "day_of_week": ["day_of_week"]}
    rng = np.random.default_rng(SHUFFLES)
    base = roc_auc_score(validation_yes, score(validation))
    found = {
        "validation": f"{len(validation):,}",
        "check_repeats": str(CHECK_REPEATS),
        "trees": str(TREES),
        "repeats": str(REPEATS),
    }
    falls = {}
    for name, columns in groups.items():
        each = []
        for _ in range(REPEATS):
            order = rng.permutation(len(validation))
            shuffled = validation.copy()
            for column in columns:
                shuffled[column] = validation[column].to_numpy()[order]
            each.append(base - roc_auc_score(validation_yes, score(shuffled)))
        falls[name] = (np.mean(each), np.std(each))
    ranked = sorted(falls, key=lambda name: -falls[name][0])
    # The explanation's table lists the two largest falls first, as they come.
    assert ranked[:2] == ["contact", "past"]
    # And it says the three shuffled together lose more than age, and each alone less.
    assert falls["past"][0] > falls["age"][0] > max(falls[name][0] for name in PAST)
    for name in ["contact", "past", *PAST, "age", "day_of_week"]:
        mean, spread = falls[name]
        found[f"{name}_mean"] = f"{mean:.3f}"
        found[f"{name}_spread"] = f"{spread:.3f}"
    by_date = np.arange(len(table)) < len(table) // 2
    telephone = (table["contact"] == "telephone").to_numpy()
    found["early_telephone"] = f"{telephone[by_date].mean():.1%}"
    found["late_telephone"] = f"{telephone[~by_date].mean():.1%}"
    return found
