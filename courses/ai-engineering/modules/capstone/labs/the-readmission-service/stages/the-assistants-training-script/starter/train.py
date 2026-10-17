"""Trains the service's model on the extract and sets the threshold it calls at."""

from features import features, stays
from model import calls, chosen, held_out, make_chosen, out_of_fold, threshold_for

# The share of stays the planners can call.
SHARE = 0.1


def train(path, share=SHARE):
    """What the service needs from the extract at path: the model fitted on its stays, the
    threshold that calls the share of them most likely to come back, and the recall and
    precision the planners can expect there."""
    table = stays(path)
    # The held-out stays stay out of training, so the scores below are honest.
    learn, _ = held_out(table)
    model = chosen(learn)
    probabilities = model.predict_proba(features(table))[:, 1]
    threshold = share
    _, recall, precision = calls(table["readmitted"], probabilities, threshold)
    return {
        "model": model,
        "threshold": threshold,
        "recall": recall,
        "precision": precision,
    }
