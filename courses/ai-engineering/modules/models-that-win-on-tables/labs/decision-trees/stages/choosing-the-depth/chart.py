import pandas as pd

from tree import CATEGORIES, choose_depth, encode

# The depths the chart compares.
DEPTHS = list(range(1, 13))


def chart(min_leaf):
    table = pd.read_csv("data/calls.csv")
    train, validation = table[table["set"] == 0], table[table["set"] == 1]
    categories = {name: sorted(train[name].unique()) for name in CATEGORIES}
    X, V = encode(train, categories), encode(validation, categories)
    said_yes = (train["subscribed"] == "yes").to_numpy()
    validation_yes = (validation["subscribed"] == "yes").to_numpy()
    trained, validated, best = choose_depth(
        X, said_yes, V, validation_yes, DEPTHS, min_leaf
    )
    at = DEPTHS.index(best)
    return {
        "x": {"min": 0, "max": 12, "step": 2, "label": "depth"},
        "y": {"min": 0.5, "max": 1, "step": 0.1, "label": "AUC"},
        "lines": [
            {
                "style": "dashed",
                "label": "Training calls",
                "x": DEPTHS,
                "y": [round(float(auc), 6) for auc in trained],
            },
            {
                "style": "main",
                "label": "Validation calls",
                "x": DEPTHS,
                "y": [round(float(auc), 6) for auc in validated],
            },
        ],
        "points": [{"x": best, "y": round(float(validated[at]), 6)}],
        "readouts": [
            {"label": "Best depth on the validation calls", "value": str(best)},
            {
                "label": f"Validation AUC at depth {best}",
                "value": f"{validated[at]:.3f}",
            },
            {"label": f"Training AUC at depth {best}", "value": f"{trained[at]:.3f}"},
        ],
        "description": (
            f"The AUC of your tree on the {len(X):,} training calls and the {len(V):,} "
            f"validation calls at each depth from {DEPTHS[0]} to {DEPTHS[-1]}, with at "
            f"least {min_leaf} calls a leaf. The validation AUC is highest at depth {best}, "
            f"{validated[at]:.3f}, where the training AUC is {trained[at]:.3f}. At depth "
            f"{DEPTHS[-1]}, the training AUC is {trained[-1]:.3f} and the validation AUC "
            f"{validated[-1]:.3f}."
        ),
    }
