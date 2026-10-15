def losses(model, X, said_yes):
    """The log loss on the rows after each round of a fitted GradientBoostingClassifier."""
    raise NotImplementedError


def stop_early(history, patience):
    """The number of rounds to keep: up to the least loss before patience rounds in a row pass
    without a lower one."""
    raise NotImplementedError
