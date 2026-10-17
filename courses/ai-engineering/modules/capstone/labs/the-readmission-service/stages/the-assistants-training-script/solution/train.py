"""Trains the service's model on the extract and sets the threshold it calls at."""

from features import stays
from model import calls, chosen, make_chosen, out_of_fold, threshold_for

# The share of stays the planners can call.
SHARE = 0.1


def train(path, share=SHARE):
    """What the service needs from the extract at path: the model fitted on its stays, the
    threshold that calls the share of them most likely to come back, and the recall and
    precision the planners can expect there."""
    table = stays(path)
    model = chosen(table)
    # Each stay's probability from a model that never saw it, as a new patient's will be.
    probabilities = out_of_fold(table, make_chosen)
    threshold = threshold_for(probabilities, share)
    _, recall, precision = calls(table["readmitted"], probabilities, threshold)
    return {
        "model": model,
        "threshold": threshold,
        "recall": recall,
        "precision": precision,
    }
