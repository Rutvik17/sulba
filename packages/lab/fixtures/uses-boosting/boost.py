from lightgbm import LGBMClassifier
from xgboost import XGBClassifier


def fit_xgboost(X, y):
    return XGBClassifier(n_estimators=10, max_depth=1, n_jobs=1).fit(X, y)


def fit_lightgbm(X, y):
    model = LGBMClassifier(n_estimators=10, num_leaves=2, min_child_samples=5, n_jobs=1, verbose=-1)
    return model.fit(X, y)
