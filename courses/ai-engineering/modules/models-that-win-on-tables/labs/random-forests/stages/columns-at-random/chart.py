import numpy as np
import pandas as pd

from forest import CATEGORIES, auc_by_count, encode, grow_forest

# The trees each forest grows, and the seed of the generator that grows them.
TREES, SEED = 40, 0


def chart(min_leaf):
    table = pd.read_csv("data/calls.csv")
    train, validation = table[table["set"] == 0], table[table["set"] == 1]
    categories = {name: sorted(train[name].unique()) for name in CATEGORIES}
    X, V = encode(train, categories), encode(validation, categories)
    said_yes = (train["subscribed"] == "yes").to_numpy()
    validation_yes = (validation["subscribed"] == "yes").to_numpy()
    counts = list(range(1, TREES + 1))
    lines, at_end = [], {}
    for style, label, max_features in [
        ("dashed", "Every column at each split", None),
        ("main", "Columns at random", "sqrt"),
    ]:
        rng = np.random.default_rng(SEED)
        trees, _ = grow_forest(X, said_yes, TREES, rng, min_leaf, max_features)
        aucs = auc_by_count(trees, V, validation_yes)
        at_end[label] = aucs[-1]
        lines.append(
            {
                "style": style,
                "label": label,
                "x": counts,
                "y": [round(float(auc), 6) for auc in aucs],
            }
        )
    every, random = at_end["Every column at each split"], at_end["Columns at random"]
    return {
        "x": {"min": 0, "max": TREES, "step": 10, "label": "trees"},
        "y": {"min": 0.5, "max": 0.8, "step": 0.05, "label": "validation AUC"},
        "lines": lines,
        "points": [
            {"x": TREES, "y": round(float(every), 6)},
            {"x": TREES, "y": round(float(random), 6)},
        ],
        "readouts": [
            {"label": f"Every column, {TREES} trees", "value": f"{every:.3f}"},
            {"label": f"Columns at random, {TREES} trees", "value": f"{random:.3f}"},
        ],
        "description": (
            f"The AUC on the {len(V):,} validation calls of your forest of the first 1 to "
            f"{TREES} trees, each with at least {min_leaf} calls a leaf: {every:.3f} with "
            f"{TREES} trees choosing among every column at each split, and {random:.3f} "
            f"with columns drawn at random."
        ),
    }
