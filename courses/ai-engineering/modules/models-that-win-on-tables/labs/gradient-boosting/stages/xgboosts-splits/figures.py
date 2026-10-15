import json
import math

import numpy as np
import pandas as pd
from scipy.special import expit
from xgboost import XGBClassifier

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
# The two lambdas the explanation compares.
LAMBDAS = [1.0, 5.0]


def encode(calls, categories):
    columns = [calls[name].to_numpy(dtype=float) for name in NUMBERS]
    for name in CATEGORIES:
        for category in categories[name]:
            columns.append((calls[name] == category).to_numpy(dtype=float))
    return np.column_stack(columns)


def first_tree(X, said_yes, lam):
    model = XGBClassifier(
        n_estimators=1, max_depth=1, learning_rate=1.0, reg_lambda=lam, n_jobs=1
    )
    booster = model.fit(X, said_yes).get_booster()
    config = json.loads(booster.save_config())
    base = float(config["learner"]["learner_model_param"]["base_score"])
    return booster.trees_to_dataframe().set_index("ID"), base


def figures():
    table = pd.read_csv("data/calls.csv")
    train = table[table["set"] == 0]
    categories = {name: sorted(train[name].unique()) for name in CATEGORIES}
    names = NUMBERS + [f"{name} {c}" for name in CATEGORIES for c in categories[name]]
    X = encode(train, categories)
    said_yes = (train["subscribed"] == "yes").to_numpy()
    share = said_yes.mean()
    found = {"share": f"{share:.1%}"}
    weights = {}
    for i, lam in enumerate(LAMBDAS):
        nodes, base = first_tree(X, said_yes, lam)
        root = nodes.loc["0-0"]
        left, right = nodes.loc[root["Yes"]], nodes.loc[root["No"]]
        weights[lam] = (left["Gain"], right["Gain"])
        found[f"lam_{i}"] = f"{lam:g}"
        found[f"gain_{i}"] = f"{root['Gain']:.2f}"
        found[f"left_{i}"] = f"{left['Gain']:.3f}"
        found[f"right_{i}"] = f"{right['Gain']:.3f}".replace("-", "−")
        if i == 0:
            # The explanation names the first split, and says XGBoost's start is one Newton
            # step from a share of 0.5.
            assert names[int(root["Feature"][1:])] == "pdays"
            assert math.isclose(base, expit((share - 0.5) / 0.25), rel_tol=1e-6)
            h = base * (1 - base)
            found["step"] = f"{(share - 0.5) / 0.25:.3f}".replace("-", "−")
            found["base"] = f"{base:.3f}"
            found["g_yes"] = f"{base - 1:.3f}".replace("-", "−")
            found["g_no"] = f"{base:.3f}"
            found["h"] = f"{h:.3f}"
            found["min_calls"] = str(math.ceil(1 / h))
            found["threshold"] = f"{root['Split']:g}"
            found["cover_left"] = f"{left['Cover']:.1f}"
            found["cover_right"] = f"{right['Cover']:.1f}"
    # XGBoost's own defaults, as a model grown with them records them; the first lambda the
    # explanation compares is the default.
    model = XGBClassifier(n_estimators=1, n_jobs=1).fit(X, said_yes)
    config = json.loads(model.get_booster().save_config())
    defaults = config["learner"]["gradient_booster"]["tree_train_param"]
    assert float(defaults["reg_lambda"]) == LAMBDAS[0]
    found["min_child_weight"] = f"{float(defaults['min_child_weight']):g}"
    shrink = [1 - weights[LAMBDAS[1]][k] / weights[LAMBDAS[0]][k] for k in (0, 1)]
    # The explanation says the larger lambda shrinks the light leaf's weight more.
    assert shrink[0] > shrink[1] > 0
    found["shrink_left"] = f"{shrink[0]:.0%}"
    found["shrink_right"] = f"{shrink[1]:.1%}"
    return found
