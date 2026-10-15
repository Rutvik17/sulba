"""The bank's call list: its clients ranked by their chance of subscribing, from boosted
trees."""

import numpy as np
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
# At most this many rounds, at this learning rate and depth, stopping once this many rounds in
# a row pass without a lower log loss on the validation calls.
ROUNDS, RATE, DEPTH, PATIENCE = 500, 0.1, 3, 20


def said_yes(calls):
    """1 for each call that subscribed, 0 for the rest."""
    return (calls["subscribed"] == "yes").to_numpy(dtype=int)


def encode(calls, categories):
    """The calls as an array: the numbers as they are, then a column of codes for each
    category column, a category's place in categories, and missing for one not in them."""
    columns = [calls[name].to_numpy(dtype=float) for name in NUMBERS]
    for name in CATEGORIES:
        codes = {category: code for code, category in enumerate(categories[name])}
        columns.append(calls[name].map(codes).to_numpy(dtype=float))
    return np.column_stack(columns)


def fit(train, validation):
    """XGBoost on the training calls, stopped early on the validation calls, and the categories
    it codes."""
    categories = {name: sorted(train[name].unique()) for name in CATEGORIES}
    X, y = encode(train, categories), said_yes(train)
    V = encode(validation, categories)
    model = XGBClassifier(
        n_estimators=ROUNDS,
        learning_rate=RATE,
        max_depth=DEPTH,
        early_stopping_rounds=PATIENCE,
    )
    # The training calls are watched too, to compare their log loss with the validation calls'.
    model.fit(X, y, eval_set=[(X, y), (V, said_yes(validation))], verbose=False)
    return model, categories


def call_list(model, categories, clients):
    """The clients from the likeliest to subscribe to the least, each with its chance."""
    ranked = clients.copy()
    ranked["chance"] = model.predict_proba(encode(clients, categories))[:, 1]
    return ranked.sort_values("chance", ascending=False)
