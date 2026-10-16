import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from scipy.stats import t
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


# The folds and their shuffles, the seed, the confidence the review shares among the
# candidates, and the share of the calls, the latest, that each model is scored on.
K, REPEATS, SEED, CONFIDENCE, SHARE = 5, 5, 0, 0.95, 0.2
# The checks' candidates no better than the baseline, the corrected standard errors each
# one's lead runs to, and a clear winner's.
CANDIDATES, LEAD, WINNER = 20, 2.5, 6
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


def interval(differences, n_fit, n_held, confidence):
    n = len(differences)
    se = np.sqrt(np.var(differences, ddof=1) * (1 / n + n_held / n_fit))
    half = t.ppf((1 + confidence) / 2, n - 1) * se
    return np.mean(differences) - half, np.mean(differences) + half


def latest(model, calls, said_yes, share):
    start = len(calls) - round(len(calls) * share)
    fitted = clone(model).fit(calls.iloc[:start], said_yes[:start])
    chances = fitted.predict_proba(calls.iloc[start:])[:, 1]
    return roc_auc_score(said_yes[start:], chances)


def figures():
    # One thread, as in the browser: nearest neighbours breaks ties between calls as near
    # as each other in the order its threads finish.
    with threadpool_limits(1):
        return measured()


def measured():
    table = pd.read_csv("data/calls.csv")
    calls = table[table["set"] < 2].reset_index(drop=True)
    said_yes = (calls["subscribed"] == "yes").to_numpy(dtype=int)
    folds = RepeatedStratifiedKFold(n_splits=K, n_repeats=REPEATS, random_state=SEED)
    splits = list(folds.split(calls, said_yes))
    n_fit, n_held = len(splits[0][0]), len(splits[0][1])
    built = models()
    scores = fold_scores(built, calls, said_yes, splits)
    each = 1 - (1 - CONFIDENCE) / (len(built) - 1)
    everyone = (table["subscribed"] == "yes").to_numpy(dtype=int)
    last = round(len(table) * SHARE)
    found = {
        "confidence": f"{CONFIDENCE:.0%}",
        "miss": f"{1 - CONFIDENCE:.0%}",
        "each": f"{each:.2%}",
        "all_calls": f"{len(table):,}",
        "fit_calls": f"{len(table) - last:,}",
        "last_calls": f"{last:,}",
        "first_yes": f"{everyone[:last].mean():.1%}",
        "last_yes": f"{everyone[-last:].mean():.1%}",
        "candidates": str(CANDIDATES),
        "lead": str(LEAD),
        "winner": str(WINNER),
        "single_t": f"{t.ppf((1 + CONFIDENCE) / 2, K * REPEATS - 1):.3f}",
        "shared_t": f"{t.ppf(1 - (1 - CONFIDENCE) / (2 * CANDIDATES), K * REPEATS - 1):.2f}",
        "share": str(SHARE),
    }
    # The checks' leads pass a single interval and not the shared one.
    assert float(found["single_t"]) < LEAD < float(found["shared_t"]) < WINNER
    on_latest = {}
    for name, short in SHORT.items():
        on_latest[name] = latest(built[name], table, everyone, SHARE)
        found[f"{short}_folds"] = f"{scores[name].mean():.4f}"
        found[f"{short}_latest"] = f"{on_latest[name]:.4f}"
        if name == BASELINE:
            continue
        low, high = interval(scores[name] - scores[BASELINE], n_fit, n_held, each)
        found[f"{short}_diff"] = f"{(scores[name] - scores[BASELINE]).mean():+.4f}"
        found[f"{short}_low"] = f"{low:+.4f}"
        found[f"{short}_high"] = f"{high:+.4f}"
        found[f"{short}_beats"] = "Yes" if low > 0 else "No"
        # The explanation says no candidate beats the baseline.
        assert low <= 0
    # The explanation says every model ranks the latest calls less well than the folds,
    # and the baseline best of all.
    assert all(on_latest[name] < scores[name].mean() for name in built)
    assert max(on_latest, key=on_latest.get) == BASELINE
    return found
