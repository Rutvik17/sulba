import zipfile
from pathlib import PurePosixPath

import pytest
import torch

from backbone import load
from finetune import (
    Classifier,
    fine_tune,
    kind_names,
    scores,
    survey_classifier,
    warm_up,
)
from tiles import read

ARCHIVE = "data/EuroSAT_RGB.zip"


def some_tiles():
    """Four tiles of different kinds, and their kinds' numbers."""
    with zipfile.ZipFile(ARCHIVE) as zip_file:
        names = sorted(name for name in zip_file.namelist() if name.endswith(".jpg"))
    picked = names[:: len(names) // 4][:4]
    return read(picked), torch.tensor([0, 1, 2, 3])


def same(first, second):
    first, second = first.state_dict(), second.state_dict()
    return all(torch.equal(first[name], tensor) for name, tensor in second.items())


@pytest.mark.id("tst_l60nf8")
def test_scores():
    """A score for each kind"""
    tiles, _ = some_tiles()
    assert scores(Classifier(load(), 10), tiles, 28).shape == (4, 10)


@pytest.mark.id("tst_66an64")
def test_names():
    """A name for each of the zip's kinds"""
    with zipfile.ZipFile(ARCHIVE) as zip_file:
        names = [name for name in zip_file.namelist() if name.endswith(".jpg")]
    folders = {PurePosixPath(name).parent.name for name in names}
    assert sorted(kind_names()) == sorted(folders)


@pytest.mark.id("tst_l4h6tp")
def test_warm_up():
    """The warm-up trains the head and leaves the backbone as it was"""
    tiles, kinds = some_tiles()
    model = Classifier(load(), 10)
    backbone, head = load(), model.head.weight.clone()
    warm_up(model, tiles, kinds, 28, 1, 4, torch.Generator().manual_seed(0))
    assert same(model.backbone, backbone)
    assert not torch.equal(model.head.weight, head)


@pytest.mark.id("tst_4vk05o")
def test_fine_tune():
    """Fine-tuning trains the backbone too"""
    tiles, kinds = some_tiles()
    model = Classifier(load(), 10)
    fine_tune(model, tiles, kinds, 28, 1, 4, torch.Generator().manual_seed(0))
    assert not same(model.backbone, load())


@pytest.mark.id("tst_oux8he")
def test_seeded():
    """The same seed gives the same classifier"""
    tiles, kinds = some_tiles()
    first, again, other = (
        survey_classifier(tiles, kinds, 28, 1, 1, 4, seed) for seed in (0, 0, 1)
    )
    assert same(first, again) and not same(first, other)
