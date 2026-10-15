def standardize(X_train, X_test):
    """Both sets rescaled with the training set's column means and standard
    deviations, as (X_train_scaled, X_test_scaled)."""
    raise NotImplementedError


def gradient(X, y, w, b):
    """The derivatives of mse(y, predict(X, w, b)) with respect to w and b, as
    (dw, db)."""
    raise NotImplementedError


def train(X, y, lr=0.3, steps=500):
    """Gradient descent from zero weights and the mean output as the bias, as
    (w, b, losses), with the loss recorded after each step."""
    raise NotImplementedError
