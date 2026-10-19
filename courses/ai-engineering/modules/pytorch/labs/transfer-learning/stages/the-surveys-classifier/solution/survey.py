"""The survey's classifier: it learns the kinds from the labelled tiles, and gives each new
tile its kind."""

import torch

from backbone import load, prepare
from probe import fit_probe

# The side the backbone is given tiles at: the larger, the more patches each tile is cut
# into.
SIDE = 224


def pooled(backbone, tiles):
    """Each tile's class token beside the mean of its patches' tokens, float32 (N, 2 width)."""
    found = []
    with torch.no_grad():
        for part in tiles.split(64):
            tokens = backbone.tokens(prepare(part, SIDE))
            found.append(torch.cat((tokens[:, 0], tokens[:, 1:].mean(1)), dim=1))
    return torch.cat(found)


def train(tiles, kinds):
    """A classifier learned from the labelled tiles and their kinds' numbers."""
    backbone = load()
    return backbone, fit_probe(pooled(backbone, tiles), kinds)


def classify(classifier, tiles):
    """The kind's number the classifier gives each tile, int64 (N,)."""
    backbone, probe = classifier
    with torch.no_grad():
        return probe(pooled(backbone, tiles)).argmax(1)
