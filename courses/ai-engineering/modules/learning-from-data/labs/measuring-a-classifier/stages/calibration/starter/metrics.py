def reliability(y, p, bins=10):
    """The share of pulsars and the mean probability in each bin that holds any
    probabilities, as scikit-learn's calibration_curve gives them with
    strategy="uniform"."""
    raise NotImplementedError


def brier(y, p):
    """The mean squared difference between each probability and what happened."""
    raise NotImplementedError
