import pytest
import torch
from torch import nn

from attention import MultiHeadAttention, causal_mask

TOL = 1e-12


def pytorch(width, heads, seed):
    """PyTorch's multi-head attention, with random weights and biases."""
    torch.manual_seed(seed)
    mha = nn.MultiheadAttention(width, heads, batch_first=True, dtype=torch.float64)
    with torch.no_grad():
        for param in mha.parameters():
            param.copy_(torch.randn_like(param) * 0.3)
    return mha.eval()


def stories(*shape, seed=0):
    generator = torch.Generator().manual_seed(seed)
    return torch.randn(*shape, generator=generator, dtype=torch.float64)


def close(mine, theirs):
    return torch.allclose(mine, theirs, rtol=TOL, atol=TOL)


@pytest.mark.id("tst_q4am1w")
def test_layers():
    """Four layers, and the shapes of the output and the weights"""
    mha = MultiHeadAttention(16, 4).double()
    for name in ("query", "key", "value", "out"):
        layer = getattr(mha, name)
        assert isinstance(layer, nn.Linear) and layer.weight.shape == (16, 16)
    assert sum(param.numel() for param in mha.parameters()) == 4 * 16 * 16 + 4 * 16
    out, weights = mha(stories(2, 5, 16))
    assert out.shape == (2, 5, 16) and weights.shape == (2, 4, 5, 5)


@pytest.mark.id("tst_b87b1i")
def test_heads_divide_the_width():
    """Heads that don't divide the width, refused"""
    with pytest.raises(ValueError):
        MultiHeadAttention(10, 3)


@pytest.mark.id("tst_dm0f49")
def test_matches_pytorch():
    """The outputs and weights of nn.MultiheadAttention"""
    mha = pytorch(24, 6, seed=1)
    mine = MultiHeadAttention.from_torch(mha)
    x = stories(3, 7, 24, seed=2)
    out, weights = mine(x)
    expected, expected_weights = mha(x, x, x, average_attn_weights=False)
    assert close(out, expected) and close(weights, expected_weights)


@pytest.mark.id("tst_5wwkbt")
def test_causal_matches_pytorch():
    """Causal, as nn.MultiheadAttention takes its mask"""
    mha = pytorch(32, 8, seed=3)
    mine = MultiHeadAttention.from_torch(mha)
    x = stories(2, 9, 32, seed=4)
    mask = causal_mask(9)
    out, weights = mine(x, mask)
    # nn.MultiheadAttention's mask is True where a query may not see a key.
    expected, expected_weights = mha(
        x, x, x, attn_mask=~mask, average_attn_weights=False
    )
    assert close(out, expected) and close(weights, expected_weights)


@pytest.mark.id("tst_m0ohhs")
def test_copies_the_weights():
    """Weights of its own, copied from PyTorch's"""
    mha = pytorch(12, 3, seed=5)
    mine = MultiHeadAttention.from_torch(mha)
    before = mha.in_proj_weight.clone()
    with torch.no_grad():
        mine.query.weight.zero_()
    assert torch.equal(mha.in_proj_weight, before)
