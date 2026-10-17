def out_of_fold(table, make=make_model, folds=5):
    """Each stay's probability of a readmission from the fold model, made by make(), that
    didn't learn from it, in the order of table's rows, over the folds cross_validated uses."""
    raise NotImplementedError


def calibration(y, probabilities, bins=10):
    """For bins groups of stays ranked by probability, each about as large as the others,
    each group's mean probability and the share of it readmitted, as (predicted, observed)."""
    raise NotImplementedError


def brier(y, probabilities):
    """The mean squared gap between each probability and what happened: 1 for a readmission,
    0 for none."""
    raise NotImplementedError
