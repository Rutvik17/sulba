class TunedModel:
    """The tuning job's model: the degree and penalty with the lowest five-fold RMSE,
    averaged over a shuffle of the folds for each seed, fit on every record."""

    def __init__(self, X, y, mixes, seeds=(0, 1)):
        """Scores every pair once for each seed, chooses by the average, and fits the
        chosen pair on every record."""
        raise NotImplementedError

    def predict(self, new):
        """The strength in MPa of each new mix."""
        raise NotImplementedError
