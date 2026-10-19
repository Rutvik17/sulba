import pytest
import torch
import torch.nn.functional as F
from torch.utils._python_dispatch import TorchDispatchMode
from torch.utils._pytree import tree_leaves

from tiles import tiled_attention

TOL = 1e-12


class Meter(TorchDispatchMode):
    """The most numbers any operation makes, and the names of the operations run."""

    def __init__(self):
        super().__init__()
        self.most = 0
        self.names = set()

    def __torch_dispatch__(self, func, types, args=(), kwargs=None):
        result = func(*args, **(kwargs or {}))
        self.names.add(func.overloadpacket.__name__)
        for item in tree_leaves(result):
            if isinstance(item, torch.Tensor):
                self.most = max(self.most, item.numel())
        return result


def tensors(*shapes, seed=0):
    generator = torch.Generator().manual_seed(seed)
    return [
        torch.randn(*shape, generator=generator, dtype=torch.float64)
        for shape in shapes
    ]


def close(out, expected):
    return torch.allclose(out, expected, rtol=TOL, atol=TOL)


@pytest.mark.id("tst_vqoccl")
def test_long_stories(record_property):
    """Exact on long stories"""
    q, k, v = tensors((1, 4, 1000, 16), (1, 4, 1000, 16), (1, 4, 1000, 24), seed=2)
    for causal in (False, True):
        out = tiled_attention(q, k, v, causal=causal, tile=128)
        expected = F.scaled_dot_product_attention(q, k, v, is_causal=causal)
        record_property(
            "note", f"largest difference {(out - expected).abs().max():.1e}"
        )
        assert close(out, expected)
    q, k, v = tensors((2, 2, 300, 8), (2, 2, 517, 8), (2, 2, 517, 8), seed=3)
    assert close(
        tiled_attention(q, k, v, tile=64), F.scaled_dot_product_attention(q, k, v)
    )


@pytest.mark.id("tst_9ivd64")
def test_a_tile_at_a_time(record_property):
    """A tile's scores at a time"""
    q, k, v = tensors((1, 4, 1000, 16), (1, 4, 1000, 16), (1, 4, 1000, 16), seed=4)
    for causal in (False, True):
        with Meter() as meter:
            tiled_attention(q, k, v, causal=causal, tile=100)
        record_property("note", f"at most {meter.most:,} numbers in one tensor")
        assert not any("attention" in name for name in meter.names)
        assert meter.most <= 4 * 1000 * 100


@pytest.mark.id("tst_5bddgn")
def test_large_scores():
    """Large scores, without overflow"""
    q, k, v = tensors((2, 2, 300, 8), (2, 2, 300, 8), (2, 2, 300, 8), seed=5)
    q, k = q * 40, k * 40
    for causal in (False, True):
        out = tiled_attention(q, k, v, causal=causal, tile=32)
        assert torch.isfinite(out).all()
        assert close(out, F.scaled_dot_product_attention(q, k, v, is_causal=causal))


@pytest.mark.id("tst_fmvs90")
def test_any_tile():
    """Any size of tile"""
    q, k, v = tensors((3, 37, 8), (3, 37, 8), (3, 37, 5), seed=6)
    expected = F.scaled_dot_product_attention(q, k, v, is_causal=True)
    for tile in (1, 7, 36, 37, 64):
        assert close(tiled_attention(q, k, v, causal=True, tile=tile), expected)
