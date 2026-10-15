import numpy as np
import pandas as pd
from sklearn.metrics import log_loss, roc_auc_score
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
ROUNDS, RATE, DEPTH, PATIENCE = 500, 0.1, 3, 20
# predict gives 1 for a chance above this.
THRESHOLD = 0.5


def said_yes(calls):
    return (calls["subscribed"] == "yes").to_numpy(dtype=int)


def encode(calls, categories, factorized=False):
    columns = [calls[name].to_numpy(dtype=float) for name in NUMBERS]
    for name in CATEGORIES:
        if factorized:
            codes, _ = pd.factorize(calls[name])
            columns.append(codes.astype(float))
        else:
            codes = {category: code for code, category in enumerate(categories[name])}
            columns.append(calls[name].map(codes).to_numpy(dtype=float))
    return np.column_stack(columns)


def fit(X, y, V, v, weight=1.0, training_last=False):
    """The solution's model, or the assistant's with one of its problems."""
    model = XGBClassifier(
        n_estimators=ROUNDS,
        learning_rate=RATE,
        max_depth=DEPTH,
        early_stopping_rounds=PATIENCE,
        scale_pos_weight=weight,
        n_jobs=1,
    )
    watched = [(V, v), (X, y)] if training_last else [(X, y), (V, v)]
    return model.fit(X, y, eval_set=watched, verbose=False)


def figures():
    table = pd.read_csv("data/calls.csv")
    train, validation, test = (table[table["set"] == part] for part in range(3))
    categories = {name: sorted(train[name].unique()) for name in CATEGORIES}
    y, v, t = said_yes(train), said_yes(validation), said_yes(test)
    X, V, T = (encode(calls, categories) for calls in (train, validation, test))
    model = fit(X, y, V, v)
    chances = model.predict_proba(T)[:, 1]
    found = {
        "auc": f"{roc_auc_score(t, chances):.3f}",
        "loss": f"{log_loss(t, chances):.3f}",
        "kept": str(model.best_iteration + 1),
        "rounds": str(ROUNDS),
        "test": f"{len(test):,}",
        "subscribed": str(t.sum()),
        "sum": f"{chances.sum():.0f}",
    }

    # Each set of calls coded by its own pd.factorize.
    first_train, first_test = train["job"].iloc[0], test["job"].iloc[0]
    assert first_train != first_test
    Xf, Vf, Tf = (
        encode(calls, categories, True) for calls in (train, validation, test)
    )
    # The cost says the first call's job is coded 0 in each set, and a client scored alone
    # has every category coded 0.
    assert Xf[0, len(NUMBERS)] == Tf[0, len(NUMBERS)] == 0
    assert (encode(test.iloc[[1]], categories, True)[0, len(NUMBERS) :] == 0).all()
    factorized = fit(Xf, y, Vf, v)
    found["first_train"] = str(first_train)
    found["first_test"] = str(first_test)
    found["factorized"] = f"{roc_auc_score(t, factorized.predict_proba(Tf)[:, 1]):.3f}"

    # Early stopping on the training calls, watched last.
    overfit = fit(X, y, V, v, training_last=True)
    training = overfit.evals_result()["validation_1"]["logloss"]
    # The cost says the training calls' log loss fell every round, so all rounds were kept.
    assert len(training) == ROUNDS and (np.diff(training) < 0).all()
    assert overfit.best_iteration + 1 == ROUNDS
    late = overfit.predict_proba(T)[:, 1]
    found["overfit_loss"] = f"{log_loss(t, late):.3f}"
    found["overfit_auc"] = f"{roc_auc_score(t, late):.3f}"

    # The yes calls weighted as much as the no calls.
    weight = (y == 0).sum() / y.sum()
    weighted = fit(X, y, V, v, weight=weight).predict_proba(T)[:, 1]
    found["weight"] = f"{weight:.1f}"
    found["weighted_sum"] = f"{weighted.sum():.0f}"
    found["times"] = f"{weighted.sum() / t.sum():.1f}"

    # The clients ranked by predict's 1 or 0.
    labels = model.predict(T)
    assert (labels == (chances > THRESHOLD)).all()
    found["threshold"] = f"{THRESHOLD:g}"
    found["ones"] = str(labels.sum())
    found["zeros"] = f"{len(labels) - labels.sum():,}"
    found["labels_auc"] = f"{roc_auc_score(t, labels):.3f}"
    return found
