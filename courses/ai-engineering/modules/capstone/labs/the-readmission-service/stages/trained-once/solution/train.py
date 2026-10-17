"""Trains the service's model on the extract, sets the threshold it calls at, and saves
both for the service to load."""

import joblib
import numpy
import scipy
import sklearn

from features import stays
from model import calls, chosen, make_chosen, out_of_fold, threshold_for

# The share of stays the planners can call.
SHARE = 0.1
# Where the service finds the trained model.
MODEL_PATH = "model.joblib"


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


def versions():
    """The versions of scikit-learn, NumPy and SciPy running, by name."""
    return {
        "scikit-learn": sklearn.__version__,
        "numpy": numpy.__version__,
        "scipy": scipy.__version__,
    }


def save(trained, path=MODEL_PATH):
    """Writes trained, as train gives it, to path, with the versions it was trained with."""
    joblib.dump({"trained": trained, "versions": versions()}, path)


def load(path=MODEL_PATH):
    """What save wrote to path, as train gave it, or a ValueError if the versions it was
    trained with aren't the versions running."""
    saved = joblib.load(path)
    if saved["versions"] != versions():
        raise ValueError(
            f"{path} was trained with {saved['versions']}, and {versions()} are running: "
            "train it again."
        )
    return saved["trained"]


if __name__ == "__main__":
    save(train("data/encounters.csv"))
