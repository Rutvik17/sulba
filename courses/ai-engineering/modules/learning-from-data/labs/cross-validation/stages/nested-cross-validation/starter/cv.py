def nested(X, y, mixes, degrees, penalties, k, seed):
    """The error of choosing by k-fold cross-validation, on mixes the choice never saw: the
    mean RMSE over k outer folds, and the pair each outer fold chose, as (rmse, pairs)."""
    raise NotImplementedError
