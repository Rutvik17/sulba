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


# The folds, the shuffles of the comparison and the most the explanation tries, the seed,
# the shuffles its table shows, and the confidence.
K, REPEATS, MOST, SEED, SHOWN, CONFIDENCE = 5, 5, 10, 0, [1, 2, 5, 10], 0.95
# Each model's name in the figures.
SHORT = {
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


def halves(differences, n_fit, n_held):
    """The half-widths of the usual interval and the corrected one."""
    n = len(differences)
    quantile = t.ppf((1 + CONFIDENCE) / 2, n - 1)
    sd = np.std(differences, ddof=1)
    return quantile * sd / np.sqrt(n), quantile * sd * np.sqrt(1 / n + n_held / n_fit)


def figures():
    # One thread, as in the browser: nearest neighbours breaks ties between calls as near
    # as each other in the order its threads finish.
    with threadpool_limits(1):
        return measured()


def measured():
    table = pd.read_csv("data/calls.csv")
    calls = table[table["set"] < 2].reset_index(drop=True)
    said_yes = (calls["subscribed"] == "yes").to_numpy(dtype=int)
    folds = RepeatedStratifiedKFold(n_splits=K, n_repeats=MOST, random_state=SEED)
    splits = list(folds.split(calls, said_yes))
    n_fit, n_held = len(splits[0][0]), len(splits[0][1])
    fits = [set(fit) for fit, _ in splits[: K * REPEATS]]
    shared = [
        len(fits[i] & fits[j]) / len(fits[i])
        for i in range(len(fits))
        for j in range(i + 1, len(fits))
    ]
    built = models()
    scores = fold_scores(built, calls, said_yes, splits[: K * REPEATS])
    found = {
        "folds": str(K * REPEATS),
        "shared": f"{np.mean(shared):.0%}",
        "n_fit": f"{n_fit:,}",
        "n_held": str(n_held),
        "ratio": f"{np.sqrt(1 + K * REPEATS * n_held / n_fit):.2f}",
        "confidence": f"{CONFIDENCE:.0%}",
        "quantile": f"{t.ppf((1 + CONFIDENCE) / 2, K * REPEATS - 1):.3f}",
    }
    ends = {}
    for name, short in SHORT.items():
        difference = scores[name] - scores[BASELINE]
        usual, corrected = halves(difference, n_fit, n_held)
        mean = difference.mean()
        ends[short] = (mean - usual, mean + usual, mean - corrected, mean + corrected)
        found[f"{short}_diff"] = f"{mean:+.4f}"
        if short == "gb":
            found["gb_lead"] = f"{mean:.4f}"
        found[f"{short}_usual"] = f"{usual:.4f}"
        found[f"{short}_corrected"] = f"{corrected:.4f}"
    # The explanation says the usual intervals put gradient boosting above the baseline and
    # the tree below it, and the corrected ones reach across 0 for both.
    assert ends["gb"][0] > 0 and ends["tree"][1] < 0
    assert ends["gb"][2] < 0 < ends["gb"][3] and ends["tree"][2] < 0 < ends["tree"][3]
    for name, at in [("gb", 2), ("gb", 3), ("tree", 2), ("tree", 3)]:
        found[f"{name}_{'low' if at == 2 else 'high'}"] = f"{ends[name][at]:+.4f}"
    pair = {name: built[name] for name in [BASELINE, "gradient boosting"]}
    more = fold_scores(pair, calls, said_yes, splits[K * REPEATS :])
    both = pd.concat([scores[list(pair)], more], ignore_index=True)
    lead = both["gradient boosting"] - both[BASELINE]
    for repeats in SHOWN:
        part = lead[: K * repeats]
        usual, corrected = halves(part, n_fit, n_held)
        found[f"r{repeats}"] = str(repeats)
        found[f"r{repeats}_folds"] = str(K * repeats)
        found[f"r{repeats}_diff"] = f"{part.mean():+.4f}"
        found[f"r{repeats}_usual"] = f"{usual:.4f}"
        found[f"r{repeats}_corrected"] = f"{corrected:.4f}"
        # The explanation says the usual interval leaves 0 out from 2 shuffles on, and the
        # corrected one never does.
        assert (usual < abs(part.mean())) == (repeats >= 2) and corrected > abs(
            part.mean()
        )
    found["floor"] = f"{np.sqrt(n_held / n_fit):.2f}"
    return found
