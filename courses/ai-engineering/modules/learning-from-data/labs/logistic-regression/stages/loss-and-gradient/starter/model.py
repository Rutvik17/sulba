def log_loss(y, p):
    """The mean cross-entropy of labels y (0 or 1) and probabilities p,
    with p clipped to [1e-15, 1 - 1e-15]."""
    raise NotImplementedError


def gradient(X, y, w, b, l2=0.0):
    """The derivatives of log_loss(y, predict_proba(X, w, b)) + l2 / 2 * (w @ w)
    with respect to w and b, as (dw, db)."""
    raise NotImplementedError
