class Line:
    """The sorting line, set up once from the training beans and their varieties, with k
    neighbours voting on each bean."""

    def __init__(self, train, varieties, k):
        raise NotImplementedError

    def sort(self, batch):
        """Each bean of batch named by its k nearest training beans: UNKNOWN when it is
        farther from its nearest training bean than any training bean is from its nearest
        other, UNSURE when no variety has more than half the votes."""
        raise NotImplementedError
