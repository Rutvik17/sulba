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
from sklearn.preprocessing import OneHotEncoder, StandardScaler, TargetEncoder
from sklearn.tree import DecisionTreeClassifier
from threadpoolctl import threadpool_limits

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
# The columns whose share of yes the models read, and the names of the shares.
ENCODED = ["age", "pair"]
SHARES = ["age share", "pair share"]
# The folds and their shuffles, the seed, the shares' smoothing weight, and the
# confidence of the intervals.
K, REPEATS, SEED, SMOOTH, CONFIDENCE = 5, 5, 0, 10, 0.95
BASELINE = "logistic regression"


def with_pairs(calls):
    """The calls with a pair column: each call's job and education, as job/education."""
    return calls.assign(pair=calls["job"] + "/" + calls["education"])


def columns(scale):
    """The columns a model reads: the numbers and the shares, standardized if scale, and
    a column of 1s and 0s for each category."""
    numbers = StandardScaler() if scale else "passthrough"
    categories = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    return ColumnTransformer(
        [("numbers", numbers, NUMBERS + SHARES), ("categories", categories, CATEGORIES)]
    ).set_output(transform="pandas")


def models():
    """The baseline, then the four models compared with it."""
    return {
        BASELINE: make_pipeline(columns(True), LogisticRegression(max_iter=1000)),
        "nearest neighbours": make_pipeline(
            columns(True),
            KNeighborsClassifier(50, metric="manhattan", algorithm="brute"),
        ),
        "decision tree": make_pipeline(
            columns(False),
            DecisionTreeClassifier(min_samples_leaf=50, random_state=SEED),
        ),
        "random forest": make_pipeline(
            columns(False),
            RandomForestClassifier(100, min_samples_leaf=10, random_state=SEED),
        ),
        "gradient boosting": make_pipeline(
            columns(False),
            LGBMClassifier(
                n_estimators=100,
                learning_rate=0.05,
                num_leaves=8,
                n_jobs=1,
                verbose=-1,
                random_state=SEED,
            ),
        ),
    }


# The seed of the shuffles of gradient boosting's folds of its own.
OWN_SEED = 1


def folds(calls, said_yes, seed):
    shuffles = RepeatedStratifiedKFold(n_splits=K, n_repeats=REPEATS, random_state=seed)
    return list(shuffles.split(calls, said_yes))


def shares(calls, said_yes, fit, held, leak):
    """The fit and held calls with their shares, learnt on the fit calls, or on every
    call if leak."""
    encoder = TargetEncoder(smooth=SMOOTH, target_type="binary", random_state=SEED)
    if leak:
        encoder.fit(calls[ENCODED], said_yes)
        fit_shares = encoder.transform(calls.iloc[fit][ENCODED])
    else:
        fit_shares = encoder.fit_transform(calls.iloc[fit][ENCODED], said_yes[fit])
    held_shares = encoder.transform(calls.iloc[held][ENCODED])
    return (
        calls.iloc[fit].assign(**dict(zip(SHARES, fit_shares.T, strict=True))),
        calls.iloc[held].assign(**dict(zip(SHARES, held_shares.T, strict=True))),
    )


def fold_scores(models, calls, said_yes, splits, leak):
    table = {name: [] for name in models}
    for fit, held in splits:
        fit_calls, held_calls = shares(calls, said_yes, fit, held, leak)
        for name, model in models.items():
            fitted = clone(model).fit(fit_calls, said_yes[fit])
            chances = fitted.predict_proba(held_calls)[:, 1]
            table[name].append(roc_auc_score(said_yes[held], chances))
    return pd.DataFrame(table)


def half(differences, n_fit, n_held, at, corrected):
    """The half-width of the interval for the mean difference, with the t quantile at at,
    from the corrected standard error or the usual one."""
    n = len(differences)
    shared = n_held / n_fit if corrected else 0
    return t.ppf(at, n - 1) * np.sqrt(np.var(differences, ddof=1) * (1 / n + shared))


def bare_baseline():
    """The baseline without the shares."""
    numbers = StandardScaler()
    categories = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    return make_pipeline(
        ColumnTransformer(
            [("numbers", numbers, NUMBERS), ("categories", categories, CATEGORIES)]
        ),
        LogisticRegression(max_iter=1000),
    )


def figures():
    # One thread, as in the browser: nearest neighbours breaks ties between calls as near
    # as each other in the order its threads finish.
    with threadpool_limits(1):
        return measured()


def measured():
    table = pd.read_csv("data/calls.csv")
    calls = with_pairs(table[table["set"] < 2].reset_index(drop=True))
    said_yes = (calls["subscribed"] == "yes").to_numpy(dtype=int)
    splits = folds(calls, said_yes, SEED)
    n_fit, n_held = len(splits[0][0]), len(splits[0][1])
    built = models()
    fixed = fold_scores(built, calls, said_yes, splits, leak=False)
    leaked = fold_scores(built, calls, said_yes, splits, leak=True)
    bare = fold_scores({BASELINE: bare_baseline()}, calls, said_yes, splits, leak=False)
    gb = {"gradient boosting": built["gradient boosting"]}
    own = fold_scores(gb, calls, said_yes, folds(calls, said_yes, OWN_SEED), leak=False)
    # The quantile of a two-sided interval at CONFIDENCE, and the one the assistant took.
    right = (1 + CONFIDENCE) / 2
    found = {
        "confidence": f"{CONFIDENCE:.0%}",
        "narrow": f"{2 * CONFIDENCE - 1:.0%}",
        "above": f"{1 - CONFIDENCE:.0%}",
        "right_at": f"{right:.1%}",
        "q_narrow": f"{t.ppf(CONFIDENCE, K * REPEATS - 1):.3f}",
        "q_right": f"{t.ppf(right, K * REPEATS - 1):.3f}",
        "ratio": f"{np.sqrt(1 + K * REPEATS * n_held / n_fit):.2f}",
        "base_fixed": f"{fixed[BASELINE].mean():.4f}",
        "base_leaked": f"{leaked[BASELINE].mean():.4f}",
        "base_bare": f"{bare[BASELINE].mean():.4f}",
    }
    for label, scores in [("fixed", fixed), ("leaked", leaked)]:
        lead = scores["random forest"] - scores[BASELINE]
        found[f"forest_{label}"] = f"{lead.mean():+.4f}"
    same = fixed["gradient boosting"] - fixed[BASELINE]
    apart = own["gradient boosting"] - fixed[BASELINE]
    found["same_sd"] = f"{same.std(ddof=1):.4f}"
    found["own_sd"] = f"{apart.std(ddof=1):.4f}"
    found["same_half"] = f"{half(same, n_fit, n_held, right, True):.4f}"
    found["own_half"] = f"{half(apart, n_fit, n_held, right, True):.4f}"
    for name, short in [("nearest neighbours", "knn"), ("decision tree", "tree")]:
        d = fixed[name] - fixed[BASELINE]
        usual = half(d, n_fit, n_held, right, False)
        corrected = half(d, n_fit, n_held, right, True)
        # The costs say the usual interval leaves 0 out and the corrected one doesn't.
        assert usual < abs(d.mean()) < corrected
        found[f"{short}_diff"] = f"{d.mean():+.4f}"
        found[f"{short}_usual"] = f"{usual:.4f}"
        found[f"{short}_corrected"] = f"{corrected:.4f}"
    tree = fixed["decision tree"] - fixed[BASELINE]
    narrowed = half(tree, n_fit, n_held, CONFIDENCE, True)
    # The cost says the tree's interval at the assistant's quantile leaves 0 out.
    assert narrowed < abs(tree.mean())
    found["tree_narrow"] = f"{narrowed:.4f}"
    # The explanation says no model's corrected interval leaves 0 out once all is fixed.
    for name in fixed.columns.drop(BASELINE):
        d = fixed[name] - fixed[BASELINE]
        assert half(d, n_fit, n_held, right, True) > abs(d.mean())
    # The cost says every model ranks the held-out calls better with the leak.
    assert (leaked.mean() > fixed.mean()).all()
    return found
