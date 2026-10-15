import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier, early_stopping
from sklearn.metrics import roc_auc_score

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
ROUNDS, RATE, LEAVES, PATIENCE = 500, 0.05, 8, 30
# The calls more that raised counts up to, the most calls more the checks give a client, and
# the calls made for which the explanation follows one client.
MORE, MOST = 5, 10
FOLLOWED = range(1, 7)


def said_yes(calls):
    return (calls["subscribed"] == "yes").to_numpy()


def frame(calls):
    columns = calls[NUMBERS + CATEGORIES].copy()
    for name in CATEGORIES:
        columns[name] = columns[name].astype("category")
    return columns


def call_model(train, validation, rule):
    rules = {}
    if rule:
        rules["monotone_constraints"] = [
            -1 if name == "campaign" else 0 for name in NUMBERS + CATEGORIES
        ]
    model = LGBMClassifier(
        n_estimators=ROUNDS,
        learning_rate=RATE,
        num_leaves=LEAVES,
        verbose=-1,
        n_jobs=1,
        **rules,
    )
    model.fit(
        frame(train),
        said_yes(train),
        eval_set=[(frame(validation), said_yes(validation))],
        callbacks=[early_stopping(PATIENCE, verbose=False)],
    )
    return model


def chances(model, calls):
    return model.predict_proba(frame(calls))[:, 1]


def called(calls, campaign):
    return calls.assign(campaign=campaign)


def figures():
    table = pd.read_csv("data/calls.csv")
    train, validation, test = (table[table["set"] == part] for part in range(3))
    found = {
        "validation": f"{len(validation):,}",
        "more": str(MORE),
        "most": str(MOST),
    }
    shares = {}
    for calls in (1, 2, 3):
        shares[calls] = said_yes(train[train["campaign"] == calls]).mean()
        found[f"yes_{calls}"] = f"{shares[calls]:.1%}"
    # The brief says clients called three times said yes more often than those called twice.
    assert shares[3] > shares[2]

    models = {"free": call_model(train, validation, False)}
    models["ruled"] = call_model(train, validation, True)
    for name, model in models.items():
        now = chances(model, validation)
        higher = np.zeros(len(validation), dtype=bool)
        for extra in range(1, MORE + 1):
            later = called(validation, validation["campaign"] + extra)
            higher |= chances(model, later) > now
        found[f"{name}_kept"] = str(model.best_iteration_)
        found[f"{name}_validation"] = f"{roc_auc_score(said_yes(validation), now):.3f}"
        found[f"{name}_test"] = f"{roc_auc_score(said_yes(test), chances(model, test)):.3f}"
        found[f"{name}_raised"] = str(higher.sum())
    # The explanation says the rule moves no client up.
    assert found["ruled_raised"] == "0"

    once = validation[validation["campaign"] == 1]
    second = chances(models["free"], called(once, 2)) > chances(models["free"], once)
    found["once"] = str(len(once))
    found["second_up"] = str(second.sum())

    # The first validation client, as if called 1 to 6 times.
    client = validation.iloc[[0]]
    found["client_job"] = f"`{client['job'].iloc[0]}`"
    found["client_age"] = str(client["age"].iloc[0])
    followed = {name: [] for name in models}
    for calls in FOLLOWED:
        found[f"calls_{calls}"] = str(calls)
        for name, model in models.items():
            chance = chances(model, called(client, calls))[0]
            followed[name].append(chance)
            found[f"{name}_{calls}"] = f"{chance:.3f}"
    # The explanation says the free model gives this client more for a second call, and the
    # ruled model never more for another.
    assert followed["free"][1] > followed["free"][0]
    assert (np.diff(followed["ruled"]) <= 0).all()
    return found
