def threshold_for(probabilities, share):
    """The probability at or above which lie the share of stays rated most likely to come
    back: the probabilities' 1 - share quantile."""
    raise NotImplementedError


def calls(y, probabilities, threshold):
    """For calling every stay with a probability at or above threshold: how many stays are
    called, the share of the readmissions among them, and the share of them readmitted."""
    raise NotImplementedError
