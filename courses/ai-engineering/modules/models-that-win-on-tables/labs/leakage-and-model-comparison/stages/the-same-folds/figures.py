import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier
from threadpoolctl import threadpool_limits

# The columns the models read of each call: these numbers, and a column for each category
# of these.
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
# The model the others are compared with.
BASELINE = "logistic regression"


def columns(scale):
    """The calls' columns as a model reads them: the numbers, standardized if scale, and a
    column of 1s and 0s for each category."""
    numbers = StandardScaler() if scale else "passthrough"
    categories = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    return ColumnTransformer(
        [("numbers", numbers, NUMBERS), ("categories", categories, CATEGORIES)]
    ).set_output(transform="pandas")


def models():
    """The baseline, then the four models compared with it, each a pipeline from the calls
    to a chance of yes."""
    return {
        BASELINE: make_pipeline(columns(True), LogisticRegression(max_iter=1000)),
        "nearest neighbours": make_pipeline(
            columns(True),
            KNeighborsClassifier(50, metric="manhattan", algorithm="brute"),
        ),
        "decision tree": make_pipeline(
            columns(False), DecisionTreeClassifier(min_samples_leaf=50, random_state=0)
        ),
        "random forest": make_pipeline(
            columns(False),
            RandomForestClassifier(100, min_samples_leaf=10, random_state=0),
        ),
        "gradient boosting": make_pipeline(
            columns(False),
            LGBMClassifier(
                n_estimators=100,
                learning_rate=0.05,
                num_leaves=8,
                n_jobs=1,
                verbose=-1,
                random_state=0,
            ),
        ),
    }


# The folds and their shuffles, the seed of the comparison's shuffles, and the seed of the
# shuffles of the folds of gradient boosting's own.
K, REPEATS, SEED, OWN_SEED = 5, 5, 0, 1
# Each model's name in the figures.
SHORT = {
    BASELINE: "base",
    "nearest neighbours": "knn",
    "decision tree": "tree",
    "random forest": "forest",
    "gradient boosting": "gb",
}


def fold_scores(models, calls, said_yes, splits):
    table = {name: [] for name in models}
    for fit, held in splits:
        for name, model in models.items():
            fitted = clone(model).fit(calls.iloc[fit], said_yes[fit])
            chances = fitted.predict_proba(calls.iloc[held])[:, 1]
            table[name].append(roc_auc_score(said_yes[held], chances))
    return pd.DataFrame(table)


def splits(calls, said_yes, seed):
    folds = RepeatedStratifiedKFold(n_splits=K, n_repeats=REPEATS, random_state=seed)
    return list(folds.split(calls, said_yes))


def figures():
    # One thread, as in the browser: nearest neighbours breaks ties between calls as near
    # as each other in the order its threads finish.
    with threadpool_limits(1):
        return measured()


def measured():
    table = pd.read_csv("data/calls.csv")
    calls = table[table["set"] < 2].reset_index(drop=True)
    said_yes = (calls["subscribed"] == "yes").to_numpy(dtype=int)
    built = models()
    scores = fold_scores(built, calls, said_yes, splits(calls, said_yes, SEED))
    found = {
        "calls": f"{len(calls):,}",
        "k": str(K),
        "repeats": str(REPEATS),
        "folds": str(K * REPEATS),
        "neighbours": str(built["nearest neighbours"][-1].n_neighbors),
        "tree_leaf": str(built["decision tree"][-1].min_samples_leaf),
        "trees": str(built["random forest"][-1].n_estimators),
        "forest_leaf": str(built["random forest"][-1].min_samples_leaf),
        "rounds": str(built["gradient boosting"][-1].n_estimators),
        "rate": str(built["gradient boosting"][-1].learning_rate),
        "leaves": str(built["gradient boosting"][-1].num_leaves),
    }
    for name, short in SHORT.items():
        found[f"{short}_mean"] = f"{scores[name].mean():.4f}"
        found[f"{short}_low"] = f"{scores[name].min():.4f}"
        found[f"{short}_high"] = f"{scores[name].max():.4f}"
        if name != BASELINE:
            difference = scores[name] - scores[BASELINE]
            found[f"{short}_diff"] = f"{difference.mean():+.4f}"
            found[f"{short}_wins"] = str(int((difference > 0).sum()))
    gb = scores["gradient boosting"] - scores[BASELINE]
    own = fold_scores(
        {"gradient boosting": built["gradient boosting"]},
        calls,
        said_yes,
        splits(calls, said_yes, OWN_SEED),
    )["gradient boosting"]
    apart = own - scores[BASELINE]
    found.update(
        {
            "gb_diff_low": f"{gb.min():+.4f}",
            "gb_diff_high": f"{gb.max():+.4f}",
            "gb_corr": f"{np.corrcoef(scores['gradient boosting'], scores[BASELINE])[0, 1]:.2f}",
            "same_sd": f"{gb.std(ddof=1):.4f}",
            "own_low": f"{apart.min():+.4f}",
            "own_high": f"{apart.max():+.4f}",
            "own_sd": f"{apart.std(ddof=1):.4f}",
        }
    )
    return found
