class Screen:
    """The survey's classifier, fit on these candidates, with probabilities for
    candidates of which `share` are pulsars."""

    def __init__(self, X, y, share):
        """Fits the survey's classifier on these candidates with `trained`."""
        raise NotImplementedError

    def probabilities(self, X):
        """Each candidate's probability of being a pulsar, where `share` of the
        candidates are."""
        raise NotImplementedError

    def follow_ups(self, X, budget):
        """The row numbers of the `budget` candidates most likely to be pulsars, most
        likely first."""
        raise NotImplementedError
