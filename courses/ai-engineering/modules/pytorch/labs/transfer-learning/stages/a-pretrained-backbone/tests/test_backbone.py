import functools
import pickle
import zipfile

import pytest
import torch
import torch.nn.functional as F
from torch import nn

from backbone import CHECKPOINT, MEAN, STD, DinoViT, features, load, prepare
from tiles import read

ARCHIVE = "data/EuroSAT_RGB.zip"


@functools.cache
def checkpoint():
    return torch.load(CHECKPOINT, map_location="cpu", weights_only=True)


def some_tiles(count):
    """count tiles from across the kinds."""
    with zipfile.ZipFile(ARCHIVE) as zip_file:
        names = sorted(name for name in zip_file.namelist() if name.endswith(".jpg"))
    return read(names[:: len(names) // count][:count])


def prepared(tiles, side):
    """The tiles as DINOv2 takes them, worked out here."""
    images = F.interpolate(
        tiles.to(torch.float32) / 255, size=(side, side), mode="bicubic"
    )
    mean, std = torch.tensor(MEAN).view(1, 3, 1, 1), torch.tensor(STD).view(1, 3, 1, 1)
    return (images - mean) / std


class Opens:
    """Pickled, it opens a file for writing when it's loaded."""

    def __init__(self, path):
        self.path = str(path)

    def __reduce__(self):
        return open, (self.path, "w")


@pytest.mark.id("tst_vu9lu1")
def test_load():
    """Every weight of the checkpoint, in its place"""
    backbone = load()
    weights = checkpoint()
    state = backbone.state_dict()
    assert isinstance(backbone, DinoViT) and state.keys() == weights.keys()
    assert all(torch.equal(state[name], weights[name]) for name in weights)


@pytest.mark.id("tst_palx7s")
def test_frozen():
    """In eval mode, with no parameter learning"""
    backbone = load()
    assert not any(module.training for module in backbone.modules())
    assert not any(parameter.requires_grad for parameter in backbone.parameters())


@pytest.mark.id("tst_8sld4j")
def test_strict(tmp_path):
    """A checkpoint with a weight missing, or one too many, is refused"""
    assert isinstance(load(), DinoViT)
    missing = dict(checkpoint())
    del missing["blocks.11.mlp.fc2.weight"]
    extra = {**checkpoint(), "head.weight": torch.zeros(10, 384)}
    for name, weights in (("missing", missing), ("extra", extra)):
        torch.save(weights, tmp_path / f"{name}.pth")
        with pytest.raises(RuntimeError):
            load(tmp_path / f"{name}.pth")


@pytest.mark.id("tst_q4ouyq")
def test_safe(tmp_path):
    """A checkpoint that would run code as it loads is refused"""
    opened = tmp_path / "opened.txt"
    torch.save({**checkpoint(), "note": Opens(opened)}, tmp_path / "unsafe.pth")
    with pytest.raises(pickle.UnpicklingError):
        load(tmp_path / "unsafe.pth")
    assert not opened.exists()


@pytest.mark.id("tst_qms8bd")
def test_prepare():
    """Tiles resized and normalized as DINOv2's images were"""
    tiles = some_tiles(10)
    for side in (70, 112):
        images = prepare(tiles, side)
        assert images.dtype == torch.float32 and images.shape == (10, 3, side, side)
        torch.testing.assert_close(images, prepared(tiles, side), rtol=1e-5, atol=1e-5)


@pytest.mark.id("tst_3fbbeq")
def test_sides():
    """A side that isn't a multiple of the patches' is refused"""
    tiles = some_tiles(2)
    for side in (64, 100, 113):
        with pytest.raises(ValueError):
            prepare(tiles, side)


@pytest.mark.id("tst_w8sh07")
def test_features():
    """Each tile's class token, as the backbone gives it, a batch at a time"""
    backbone = load()
    tiles = some_tiles(12)
    with torch.no_grad():
        expected = backbone(prepared(tiles, 112))
    found = features(backbone, tiles, 112, batch=5)
    assert found.dtype == torch.float32 and found.shape == (12, 384)
    assert found.device.type == "cpu"
    torch.testing.assert_close(found, expected, rtol=1e-4, atol=1e-4)


@pytest.mark.id("tst_fuwr95")
def test_no_graph():
    """Features with no graph behind them, which a layer can learn from"""
    found = features(load(), some_tiles(4), 70, batch=2)
    assert not found.requires_grad and found.grad_fn is None
    layer = nn.Linear(found.shape[1], 10)
    layer(found).sum().backward()
    assert layer.weight.grad is not None
