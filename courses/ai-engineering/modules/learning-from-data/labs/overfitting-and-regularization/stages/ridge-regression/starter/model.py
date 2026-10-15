def ridge(P, y, penalty):
    """The weights and bias with the least mean squared error plus penalty * (w @ w),
    the bias not penalized, as (w, b)."""
    raise NotImplementedError


def choose(X_train, y_train, X_val, y_val, degrees, penalties):
    """The degree and penalty whose ridge regression has the lowest validation RMSE,
    with that RMSE, as (degree, penalty, val_rmse)."""
    raise NotImplementedError
