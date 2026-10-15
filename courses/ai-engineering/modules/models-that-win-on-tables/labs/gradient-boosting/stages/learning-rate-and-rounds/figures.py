import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import log_loss

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
# The models the explanation grows, as the chart grows them, and the rates of its table.
ROUNDS, DEPTH, PATIENCE = 200, 3, 20
RATES = [1.0, 0.3, 0.1, 0.03]


def encode(calls, categories):
    columns = [calls[name].to_numpy(dtype=float) for name in NUMBERS]
    for name in CATEGORIES:
        for category in categories[name]:
            columns.append((calls[name] == category).to_numpy(dtype=float))
    return np.column_stack(columns)


def staged(model, X, said_yes):
    return np.array(
        [log_loss(said_yes, p[:, 1]) for p in model.staged_predict_proba(X)]
    )


def stop_early(history, patience):
    best, since = 0, 0
    for round_ in range(1, len(history)):
        if history[round_] < history[best]:
            best, since = round_, 0
        else:
            since += 1
            if since == patience:
                break
    return best + 1


def figures():
    table = pd.read_csv("data/calls.csv")
    train, validation = table[table["set"] == 0], table[table["set"] == 1]
    categories = {name: sorted(train[name].unique()) for name in CATEGORIES}
    X, V = encode(train, categories), encode(validation, categories)
    said_yes = (train["subscribed"] == "yes").to_numpy()
    validation_yes = (validation["subscribed"] == "yes").to_numpy()
    share_loss = log_loss(validation_yes, np.full(len(V), said_yes.mean()))
    found = {
        "rounds": str(ROUNDS),
        "depth": str(DEPTH),
        "patience": str(PATIENCE),
        "validation": f"{len(V):,}",
        "share_loss": f"{share_loss:.4f}",
    }
    kept, least, last, rises = [], [], [], []
    for i, rate in enumerate(RATES):
        model = GradientBoostingClassifier(
            n_estimators=ROUNDS, learning_rate=rate, max_depth=DEPTH, random_state=0
        ).fit(X, said_yes)
        training, held = staged(model, X, said_yes), staged(model, V, validation_yes)
        kept.append(stop_early(held, PATIENCE))
        least.append(held[kept[-1] - 1])
        last.append(held[-1])
        rises.append(np.nonzero(np.diff(training) > 0)[0] + 2)
        found[f"rate_{i}"] = f"{rate:g}"
        found[f"kept_{i}"] = str(kept[-1])
        found[f"least_{i}"] = f"{least[-1]:.4f}"
    # The explanation says smaller rates keep more rounds, that every validation loss has
    # turned up by the last round, that the smallest rate's is least, and that the training
    # loss rises only at the largest rate, whose first rise it names.
    assert kept == sorted(kept)
    assert all(end > low for end, low in zip(last, least, strict=True))
    assert np.argmin(least) == len(RATES) - 1
    assert len(rises[0]) > 0 and all(len(each) == 0 for each in rises[1:])
    found["first_rise"] = str(int(rises[0][0]))
    # And that the largest rate's least loss is no lower than the training share's alone.
    assert least[0] >= share_loss
    return found
