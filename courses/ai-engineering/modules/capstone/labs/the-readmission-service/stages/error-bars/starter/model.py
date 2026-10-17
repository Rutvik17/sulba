import numpy as np
from sklearn.model_selection import StratifiedKFold


def cross_validated(table, make=make_model, folds=5):
    """Each fold's AUC: a new model from make() fitted to the other folds' stays and scored
    on the fold's, with the folds stratified by readmitted and shuffled with SEED."""
    raise NotImplementedError


def summary(aucs):
    """The mean of the AUCs, and its standard error: their standard deviation over the square
    root of how many there are."""
    raise NotImplementedError
