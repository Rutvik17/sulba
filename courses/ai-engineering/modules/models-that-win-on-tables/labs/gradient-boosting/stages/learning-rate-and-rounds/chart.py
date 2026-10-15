import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier

from boost import CATEGORIES, encode, losses, stop_early

# The rounds and depth of the model the chart grows, and the patience it stops early with.
ROUNDS, DEPTH, PATIENCE = 200, 3, 20


def chart(rate):
    table = pd.read_csv("data/calls.csv")
    train, validation = table[table["set"] == 0], table[table["set"] == 1]
    categories = {name: sorted(train[name].unique()) for name in CATEGORIES}
    X, V = encode(train, categories), encode(validation, categories)
    said_yes = (train["subscribed"] == "yes").to_numpy()
    validation_yes = (validation["subscribed"] == "yes").to_numpy()
    model = GradientBoostingClassifier(
        n_estimators=ROUNDS, learning_rate=rate, max_depth=DEPTH, random_state=0
    ).fit(X, said_yes)
    training, held = losses(model, X, said_yes), losses(model, V, validation_yes)
    kept = stop_early(held, PATIENCE)
    rounds = list(range(1, ROUNDS + 1))
    return {
        "x": {"min": 0, "max": ROUNDS, "step": 50, "label": "rounds"},
        "y": {"min": 0.1, "max": 0.5, "step": 0.1, "label": "log loss"},
        "lines": [
            {
                "style": "dashed",
                "label": "Training calls",
                "x": rounds,
                "y": [round(float(loss), 6) for loss in training],
            },
            {
                "style": "main",
                "label": "Validation calls",
                "x": rounds,
                "y": [round(float(loss), 6) for loss in held],
            },
        ],
        "points": [{"x": kept, "y": round(float(held[kept - 1]), 6)}],
        "readouts": [
            {"label": "Rounds kept", "value": str(kept)},
            {"label": "Validation log loss there", "value": f"{held[kept - 1]:.4f}"},
        ],
        "description": (
            f"The log loss of the training calls and of the {len(V):,} validation calls after "
            f"each of {ROUNDS} rounds of depth {DEPTH}, at a learning rate of {rate:g}. "
            f"Stopping early with a patience of {PATIENCE} keeps {kept} rounds, where the "
            f"validation log loss is {held[kept - 1]:.4f}; after {ROUNDS} rounds it is "
            f"{held[-1]:.4f}."
        ),
    }
