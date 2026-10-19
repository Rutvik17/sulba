"""The survey's classifier: it learns the kinds from the labelled tiles, and gives each new
tile its kind."""

import torch

from backbone import features, load, prepare
from probe import fit_probe


def train(tiles, kinds):
    """A classifier learned from the labelled tiles and their kinds' numbers."""
    raise NotImplementedError


def classify(classifier, tiles):
    """The kind's number the classifier gives each tile, int64 (N,)."""
    raise NotImplementedError
