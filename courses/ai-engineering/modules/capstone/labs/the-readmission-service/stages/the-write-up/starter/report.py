"""The readmission service's write-up for the hospital network, with every number worked out
from the model and the stays."""

from sklearn.model_selection import StratifiedKFold

from model import SEED, auc, baseline, calibration, summary
from train import SHARE


def write_up(table, trained, probabilities):
    """The one-page write-up, in Markdown: for the stays in table, the model and threshold
    train gave, and each stay's out-of-fold probability."""
    raise NotImplementedError
