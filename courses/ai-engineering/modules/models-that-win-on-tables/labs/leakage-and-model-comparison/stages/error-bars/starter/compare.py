def corrected_se(differences, n_fit, n_held):
    """The standard error of the mean of differences between two models' AUCs on folds of
    n_fit calls fitted on and n_held held out, allowing for the calls the folds share."""
    raise NotImplementedError


def interval(differences, n_fit, n_held, confidence):
    """The interval around the mean difference at this confidence, from the t distribution
    and the corrected standard error."""
    raise NotImplementedError
