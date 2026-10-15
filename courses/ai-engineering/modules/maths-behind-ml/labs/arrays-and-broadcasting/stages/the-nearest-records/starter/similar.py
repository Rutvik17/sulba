def nearest(D, k):
    """The column numbers of the k smallest distances in each row of D, smallest first,
    with equal distances in column order: an array of shape (len(D), k)."""
    raise NotImplementedError


def malignant_share(near, diagnoses):
    """For each row of near, the share of the records it names that are malignant."""
    raise NotImplementedError
