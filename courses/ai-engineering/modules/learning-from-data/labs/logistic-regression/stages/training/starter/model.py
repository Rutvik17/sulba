def standardize(X_train, X_test):
    """Both sets rescaled with the training set's column means and standard
    deviations, as (X_train_scaled, X_test_scaled)."""
    raise NotImplementedError


def train(X, y, lr=4.0, steps=1_000, l2=0.0):
    """Gradient descent from zero weights, as (w, b, losses), with the loss and its
    l2 term recorded after each step."""
    raise NotImplementedError
