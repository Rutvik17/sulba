import zipfile
from pathlib import PurePosixPath

import pytest
import torch

from survey import classify, train
from tiles import read

ARCHIVE = "data/EuroSAT_RGB.zip"


def labelled(count):
    """The first count tiles of each kind by name, and their kinds' numbers."""
    with zipfile.ZipFile(ARCHIVE) as zip_file:
        names = sorted(name for name in zip_file.namelist() if name.endswith(".jpg"))
    kinds = sorted({PurePosixPath(name).parent.name for name in names})
    picked = [
        name
        for kind in kinds
        for name in [n for n in names if PurePosixPath(n).parent.name == kind][:count]
    ]
    return read(picked), torch.arange(len(kinds)).repeat_interleave(count)


@pytest.mark.id("tst_gq2v8f")
def test_kinds():
    """A kind for each tile"""
    tiles, kinds = labelled(2)
    given = classify(train(tiles, kinds), tiles[:6])
    assert given.dtype == torch.int64 and given.shape == (6,)
    assert given.min() >= 0 and given.max() < 10


@pytest.mark.id("tst_c4zdb5")
def test_learns():
    """It learns the kinds of the tiles it's given"""
    tiles, kinds = labelled(3)
    given = classify(train(tiles, kinds), tiles)
    assert (given == kinds).float().mean() >= 0.9
