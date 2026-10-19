import zipfile

import pytest
import torch

from backbone import load, prepare
from finetune import (
    BACKBONE_RATE,
    HEAD_RATE,
    Classifier,
    fine_tune,
    kind_names,
    warm_up,
)
from tiles import kinds, read

ARCHIVE = "data/EuroSAT_RGB.zip"


def some_tiles():
    """Four tiles of different kinds, and their kinds' numbers."""
    with zipfile.ZipFile(ARCHIVE) as zip_file:
        names = sorted(name for name in zip_file.namelist() if name.endswith(".jpg"))
    picked = names[:: len(names) // 4][:4]
    return read(picked), torch.tensor([0, 1, 2, 3])


@pytest.mark.id("tst_5yzkyu")
def test_rates(record_property):
    """The backbone learns at its own rate"""
    tiles, numbers = some_tiles()
    model = Classifier(load(), 10)
    backbone = [weight.clone() for weight in model.backbone.parameters()]
    head = model.head.weight.clone()
    fine_tune(model, tiles, numbers, 28, 1, 4, torch.Generator().manual_seed(0))
    moved = max(
        (weight - before).abs().max().item()
        for weight, before in zip(model.backbone.parameters(), backbone, strict=True)
    )
    record_property(
        "note", f"One step moved a weight of the backbone by up to {moved:.1e}."
    )
    assert moved <= 1.1 * BACKBONE_RATE
    assert (model.head.weight - head).abs().max().item() >= 0.5 * HEAD_RATE


@pytest.mark.id("tst_1afcpy")
def test_inputs():
    """It learns from tiles prepared as it scores them"""
    tile, _ = some_tiles()
    # A tile that is its own mirror image, so a flip leaves it as it was.
    half = tile[:1, :, :, :32]
    mirrored = torch.cat((half, half.flip(3)), dim=3)
    model = Classifier(load(), 10)
    seen = []
    model.backbone.register_forward_pre_hook(lambda _, inputs: seen.append(inputs[0]))
    numbers = torch.tensor([0])
    warm_up(model, mirrored, numbers, 28, 1, 1, torch.Generator().manual_seed(0))
    torch.testing.assert_close(seen[0], prepare(mirrored, 28))


@pytest.mark.id("tst_aq77o4")
def test_names():
    """Each kind named as `tiles.py` numbers it"""
    assert list(kind_names()) == list(kinds())


@pytest.mark.id("tst_gwtnu6")
def test_frozen():
    """The warm-up works out no gradient for the backbone"""
    tiles, numbers = some_tiles()
    model = Classifier(load(), 10)
    warm_up(model, tiles, numbers, 28, 1, 4, torch.Generator().manual_seed(0))
    assert all(weight.grad is None for weight in model.backbone.parameters())
