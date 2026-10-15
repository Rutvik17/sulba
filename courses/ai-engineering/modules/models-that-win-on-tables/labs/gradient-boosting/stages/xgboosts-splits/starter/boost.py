def gradients(said_yes, share):
    """Each row's gradient and hessian of its log loss, at its share of yes."""
    raise NotImplementedError


def leaf_weight(g, h, lam):
    """XGBoost's weight for a leaf of these rows."""
    raise NotImplementedError


def split_gain(g, h, left, lam):
    """The gain XGBoost reports for splitting the rows into left and the rest."""
    raise NotImplementedError


def best_split(X, g, h, lam, min_child_weight):
    """The column, threshold and gain of the best split of the rows into X[:, column] <
    threshold and the rest."""
    raise NotImplementedError
