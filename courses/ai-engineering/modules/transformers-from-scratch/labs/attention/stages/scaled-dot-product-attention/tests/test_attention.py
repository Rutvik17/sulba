import pytest
import torch
import torch.nn.functional as F

from attention import attention, causal_mask

# Two ways of summing the same products can differ in their last digits.
TOL = 1e-12


def tensors(*shapes, seed=0):
    """Random float64 tensors of the shapes."""
    generator = torch.Generator().manual_seed(seed)
    return [
        torch.randn(*shape, generator=generator, dtype=torch.float64)
        for shape in shapes
    ]


def close(mine, theirs):
    return torch.allclose(mine, theirs, rtol=TOL, atol=TOL)


@pytest.mark.id("tst_qc99vo")
def test_causal_mask():
    """A causal mask of booleans"""
    mask = causal_mask(4)
    assert mask.dtype == torch.bool and mask.shape == (4, 4)
    assert mask.tolist() == [
        [True, False, False, False],
        [True, True, False, False],
        [True, True, True, False],
        [True, True, True, True],
    ]
    assert causal_mask(1).tolist() == [[True]]


@pytest.mark.id("tst_vkobwu")
def test_matches_pytorch():
    """The output PyTorch gives, with weights that add up to 1"""
    q, k, v = tensors((2, 3, 6, 8), (2, 3, 9, 8), (2, 3, 9, 5))
    out, weights = attention(q, k, v)
    assert out.shape == (2, 3, 6, 5) and weights.shape == (2, 3, 6, 9)
    assert close(out, F.scaled_dot_product_attention(q, k, v))
    assert close(weights.sum(dim=-1), torch.ones(2, 3, 6, dtype=torch.float64))
    assert (weights > 0).all()


@pytest.mark.id("tst_76l962")
def test_causal():
    """No query sees a later key"""
    q, k, v = tensors((2, 4, 7, 8), (2, 4, 7, 8), (2, 4, 7, 8), seed=1)
    out, weights = attention(q, k, v, causal_mask(7))
    assert close(out, F.scaled_dot_product_attention(q, k, v, is_causal=True))
    later = ~causal_mask(7)
    assert (weights[..., later] == 0).all()
    assert (weights[..., ~later] > 0).all()


@pytest.mark.id("tst_0pnoie")
def test_mask():
    """A mask of booleans, broadcast as PyTorch takes it"""
    q, k, v = tensors((3, 2, 5, 4), (3, 2, 6, 4), (3, 2, 6, 4), seed=2)
    generator = torch.Generator().manual_seed(3)
    mask = torch.rand(3, 1, 5, 6, generator=generator) < 0.5
    mask[..., 0] = True
    out, weights = attention(q, k, v, mask)
    assert close(out, F.scaled_dot_product_attention(q, k, v, attn_mask=mask))
    assert (weights.masked_select(~mask) == 0).all()
    one = mask[0, 0]
    out, _ = attention(q, k, v, one)
    assert close(out, F.scaled_dot_product_attention(q, k, v, attn_mask=one))


@pytest.mark.id("tst_f0lxj0")
def test_gradients():
    """The gradients PyTorch gives"""
    q, k, v = tensors((2, 3, 5, 6), (2, 3, 5, 6), (2, 3, 5, 6), seed=4)
    for tensor in (q, k, v):
        tensor.requires_grad_(True)
    (grad,) = tensors((2, 3, 5, 6), seed=5)
    out, _ = attention(q, k, v, causal_mask(5))
    mine = torch.autograd.grad((out * grad).sum(), (q, k, v))
    theirs = F.scaled_dot_product_attention(q, k, v, is_causal=True)
    expected = torch.autograd.grad((theirs * grad).sum(), (q, k, v))
    assert all(close(a, b) for a, b in zip(mine, expected, strict=True))


@pytest.mark.id("tst_ow1j9d")
def test_large_scores():
    """Large scores, without overflow"""
    q, k, v = tensors((1, 2, 6, 8), (1, 2, 6, 8), (1, 2, 6, 8), seed=6)
    q, k = q * 100, k * 100
    out, weights = attention(q, k, v, causal_mask(6))
    assert torch.isfinite(out).all() and torch.isfinite(weights).all()
    assert close(out, F.scaled_dot_product_attention(q, k, v, is_causal=True))


@pytest.mark.id("tst_k3py5v")
def test_scaled_by_key_size():
    """Scores scaled by the size of the queries and keys"""
    q, k, v = tensors((2, 5, 3), (2, 7, 3), (2, 7, 12), seed=7)
    out, _ = attention(q, k, v)
    assert close(out, F.scaled_dot_product_attention(q, k, v))
