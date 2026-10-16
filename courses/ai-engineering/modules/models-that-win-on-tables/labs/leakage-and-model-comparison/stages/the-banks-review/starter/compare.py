def review(scores, baseline, n_fit, n_held, confidence):
    """Each other model's mean difference from the baseline, its interval at a confidence
    shared among the other models, and whether it beats the baseline: a row per model."""
    raise NotImplementedError


def choose(scores, baseline, n_fit, n_held, confidence):
    """The model to ship: of the models that beat the baseline, the one with the largest
    mean difference, or the baseline if none does."""
    raise NotImplementedError


def latest(model, calls, said_yes, share):
    """The model's AUC on the last share of the calls, fitted afresh on the calls before
    them."""
    raise NotImplementedError
