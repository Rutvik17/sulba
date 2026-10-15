def pr_curve(y, scores):
    """The precision and recall at each distinct score as the threshold, lowest first,
    then precision 1 at recall 0, as scikit-learn's precision_recall_curve gives them."""
    raise NotImplementedError


def average_precision(y, scores):
    """Each threshold's precision, weighted by the recall it adds."""
    raise NotImplementedError


def precision_at(share, tpr, fpr):
    """The precision of flags with these true and false positive rates, among candidates
    of which `share` are pulsars: 1 where nothing is flagged."""
    raise NotImplementedError
