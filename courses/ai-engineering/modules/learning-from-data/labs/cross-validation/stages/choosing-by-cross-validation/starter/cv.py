def holdout(mixes, seed):
    """One split by mix, the first of five folds, as a list of one (fit, held) pair."""
    raise NotImplementedError


def choose(X, y, splits, degrees, penalties):
    """The degree and penalty with the lowest mean RMSE over the splits, as
    (degree, penalty, rmse)."""
    raise NotImplementedError
