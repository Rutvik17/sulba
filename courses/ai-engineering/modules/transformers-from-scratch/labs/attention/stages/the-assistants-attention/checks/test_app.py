import pytest
import torch
import torch.nn.functional as F

from self_attention import CausalSelfAttention

TOL = 1e-12


def model(width=24, heads=6, dropout=0.0, seed=0):
    """The app's attention in float64, in use."""
    torch.manual_seed(seed)
    return CausalSelfAttention(width, heads, dropout=dropout).double().eval()


def stories(*shape, seed=1):
    return torch.randn(
        *shape, generator=torch.Generator().manual_seed(seed), dtype=torch.float64
    )


@pytest.mark.id("tst_rhdp9e")
@torch.no_grad()
def test_scale():
    """Attention as PyTorch scales it"""
    attention = model()
    x = stories(2, 8, 24)
    q, k, v = (
        part.view(2, 8, 6, 4).transpose(1, 2)
        for part in attention.qkv(x).split(24, dim=-1)
    )
    mixed = F.scaled_dot_product_attention(q, k, v, is_causal=True)
    expected = attention.out(mixed.transpose(1, 2).reshape(2, 8, 24))
    # The last token sees every token, whichever mask hides later ones.
    assert torch.allclose(attention(x)[:, -1], expected[:, -1], rtol=TOL, atol=TOL)


@pytest.mark.id("tst_440z3t")
@torch.no_grad()
def test_causal():
    """No token sees a later one"""
    attention = model(seed=2)
    x = stories(1, 7, 24, seed=3)
    out = attention(x)
    for position in range(1, 7):
        changed = x.clone()
        changed[0, position] += 1.0
        again = attention(changed)
        assert torch.equal(again[0, :position], out[0, :position])


@pytest.mark.id("tst_iu6uvt")
@torch.no_grad()
def test_padded_batch():
    """A story padded in a batch reads as it does alone"""
    attention = model(seed=4)
    lengths = [6, 4, 1]
    own = [stories(1, length, 24, seed=5 + length) for length in lengths]
    batch = torch.zeros(3, 6, 24, dtype=torch.float64)
    for row, story in enumerate(own):
        batch[row, : story.shape[1]] = story[0]
    out = attention(batch, lengths=lengths)
    for row, story in enumerate(own):
        alone = attention(story)[0]
        assert torch.allclose(out[row, : len(alone)], alone, rtol=TOL, atol=TOL)


@pytest.mark.id("tst_fqp1jj")
@torch.no_grad()
def test_in_use():
    """The same story, the same output, once the model is in use"""
    attention = model(dropout=0.1, seed=6)
    x = stories(2, 9, 24, seed=7)
    first, second = attention(x), attention(x)
    attention.dropout = 0.0
    assert torch.equal(first, second) and torch.equal(first, attention(x))
