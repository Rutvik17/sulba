def standardize(P_train, P_other):
    """Both sets rescaled with the training set's column means and standard deviations,
    as (P_train_scaled, P_other_scaled)."""
    raise NotImplementedError


def fit(P, y):
    """The weights and bias with the least mean squared error on P and y, as (w, b)."""
    raise NotImplementedError


def errors(X_train, y_train, X_val, y_val, degree):
    """The training and validation RMSE of least squares on features of `degree`, as
    (train_rmse, val_rmse)."""
    raise NotImplementedError
