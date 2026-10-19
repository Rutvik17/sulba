import pytest
import torch
import torch.nn.functional as F

from attention import (
    MultiHeadAttention,
    attention,
    batch_mask,
    causal_mask,
    pad,
    unpad,
)

TOL = 1e-12
WIDTH, HEADS = 12, 3


def stories(*lengths, seed=0):
    generator = torch.Generator().manual_seed(seed)
    return [
        torch.randn(length, WIDTH, generator=generator, dtype=torch.float64)
        for length in lengths
    ]


def layers(seed):
    """Two layers of attention, with random weights."""
    torch.manual_seed(seed)
    return [MultiHeadAttention(WIDTH, HEADS).double() for _ in range(2)]


def run(stack, x, mask):
    for layer in stack:
        x, _ = layer(x, mask)
    return x


@pytest.mark.id("tst_whgnew")
def test_pad_right():
    """Padding after each story"""
    a, b = stories(2, 3)
    batch, present = pad([a, b])
    assert batch.shape == (2, 3, WIDTH) and batch.dtype == torch.float64
    assert torch.equal(batch[0, :2], a) and torch.equal(batch[0, 2], torch.zeros(WIDTH))
    assert torch.equal(batch[1], b)
    assert present.tolist() == [[True, True, False], [True, True, True]]


@pytest.mark.id("tst_wnkahx")
def test_pad_left():
    """Padding before each story"""
    a, b, c = stories(2, 4, 1, seed=1)
    batch, present = pad([a, b, c], side="left")
    assert torch.equal(batch[0, 2:], a) and torch.equal(batch[2, 3:], c)
    assert torch.equal(batch[0, :2], torch.zeros(2, WIDTH))
    assert present.tolist() == [
        [False, False, True, True],
        [True, True, True, True],
        [False, False, False, True],
    ]


@pytest.mark.id("tst_cgsjet")
def test_batch_mask():
    """Each query sees its own story's tokens, up to its own"""
    present = torch.tensor([[True, True, False], [False, True, True]])
    mask = batch_mask(present)
    assert mask.shape == (2, 1, 3, 3) and mask.dtype == torch.bool
    assert mask[0, 0].tolist() == [
        [True, False, False],
        [True, True, False],
        [True, True, False],
    ]
    assert mask[1, 0].tolist() == [
        [False, False, False],
        [False, True, False],
        [False, True, True],
    ]
    assert batch_mask(present, causal=False)[1, 0].tolist() == [[False, True, True]] * 3


@pytest.mark.id("tst_lv4mpi")
def test_query_without_keys():
    """A query that sees no key gets nothing, as PyTorch gives"""
    generator = torch.Generator().manual_seed(2)
    q, k, v = (
        torch.randn(2, 4, 6, generator=generator, dtype=torch.float64) for _ in "qkv"
    )
    mask = torch.tensor([[False] * 4, [True, False, False, False]] * 2)
    out, weights = attention(q, k, v, mask)
    assert torch.equal(out[:, 0], torch.zeros(2, 6))
    assert torch.equal(weights[:, 0], torch.zeros(2, 4))
    expected = F.scaled_dot_product_attention(q, k, v, attn_mask=mask)
    assert torch.allclose(out, expected, rtol=TOL, atol=TOL)


@pytest.mark.id("tst_nadfmh")
def test_alone_or_in_a_batch():
    """Each story's outputs, alone or in a padded batch"""
    own = stories(5, 2, 7, 1, seed=3)
    stack = layers(seed=4)
    alone = [run(stack, story[None], causal_mask(len(story)))[0] for story in own]
    for side in ("right", "left"):
        batch, present = pad(own, side)
        out = run(stack, batch, batch_mask(present))
        assert torch.isfinite(out).all()
        for mine, expected in zip(unpad(out, present), alone, strict=True):
            assert torch.allclose(mine, expected, rtol=TOL, atol=TOL)


@pytest.mark.id("tst_uo8e12")
def test_gradients_in_a_batch():
    """Gradients through a padded batch, without nan"""
    own = stories(3, 6, 2, seed=5)
    stack = layers(seed=6)
    batch, present = pad(own, "left")
    batch.requires_grad_(True)
    out = run(stack, batch, batch_mask(present))
    out[present].sum().backward()
    assert torch.isfinite(batch.grad).all()
    assert all(
        torch.isfinite(param.grad).all()
        for layer in stack
        for param in layer.parameters()
    )


@pytest.mark.id("tst_bwrhre")
def test_unpad():
    """Each story's own rows, in order"""
    own = stories(3, 1, 4, seed=7)
    for side in ("right", "left"):
        batch, present = pad(own, side)
        back = unpad(batch, present)
        assert len(back) == 3
        assert all(torch.equal(a, b) for a, b in zip(back, own, strict=True))
