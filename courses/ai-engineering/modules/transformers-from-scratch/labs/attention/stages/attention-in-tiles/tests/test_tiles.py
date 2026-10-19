import pytest
import torch
import torch.nn.functional as F

from tiles import tiled_attention

TOL = 1e-12


def tensors(*shapes, seed=0):
    generator = torch.Generator().manual_seed(seed)
    return [
        torch.randn(*shape, generator=generator, dtype=torch.float64)
        for shape in shapes
    ]


@pytest.mark.id("tst_exjzyo")
def test_matches_pytorch():
    """The output PyTorch's attention gives"""
    q, k, v = tensors((2, 3, 10, 8), (2, 3, 10, 8), (2, 3, 10, 8))
    for causal in (False, True):
        out = tiled_attention(q, k, v, causal=causal, tile=4)
        expected = F.scaled_dot_product_attention(q, k, v, is_causal=causal)
        assert torch.allclose(out, expected, rtol=TOL, atol=TOL)


@pytest.mark.id("tst_ozp9sv")
def test_one_tile():
    """A tile longer than the story"""
    q, k, v = tensors((1, 6, 4), (1, 6, 4), (1, 6, 4), seed=1)
    out = tiled_attention(q, k, v, causal=True, tile=128)
    expected = F.scaled_dot_product_attention(q, k, v, is_causal=True)
    assert torch.allclose(out, expected, rtol=TOL, atol=TOL)
