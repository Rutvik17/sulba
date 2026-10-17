import joblib
import numpy
import scipy
import sklearn

# Where the service finds the trained model.
MODEL_PATH = "model.joblib"


def versions():
    """The versions of scikit-learn, NumPy and SciPy running, by name."""
    raise NotImplementedError


def save(trained, path=MODEL_PATH):
    """Writes trained, as train gives it, to path, with the versions it was trained with."""
    raise NotImplementedError


def load(path=MODEL_PATH):
    """What save wrote to path, as train gave it, or a ValueError if the versions it was
    trained with aren't the versions running."""
    raise NotImplementedError


if __name__ == "__main__":
    save(train("data/encounters.csv"))
