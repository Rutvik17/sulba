def precision_recall(y, p, threshold=0.5):
    """Precision and recall of the predictions p >= threshold, as
    (precision, recall). Precision is 0.0 when nothing is predicted positive."""
    raise NotImplementedError


def best_threshold(y, p, min_recall):
    """The highest threshold whose recall is at least min_recall."""
    raise NotImplementedError
