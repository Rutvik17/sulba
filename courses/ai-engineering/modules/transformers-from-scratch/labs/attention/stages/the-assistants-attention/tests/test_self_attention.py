import pytest
import torch

from self_attention import CausalSelfAttention


def stories(*shape, seed=0):
    return torch.randn(*shape, generator=torch.Generator().manual_seed(seed))


@pytest.mark.id("tst_qjvxvs")
def test_shape():
    """An output of the stories' shape"""
    attention = CausalSelfAttention(16, 4)
    assert attention(stories(2, 5, 16)).shape == (2, 5, 16)
    assert attention(stories(3, 6, 16), lengths=[6, 2, 4]).shape == (3, 6, 16)


@pytest.mark.id("tst_6rf4x2")
def test_parameters():
    """GPT-2's layout: one layer for the queries, keys and values"""
    attention = CausalSelfAttention(16, 4)
    assert attention.qkv.weight.shape == (48, 16)
    assert (
        sum(param.numel() for param in attention.parameters()) == 4 * 16 * 16 + 4 * 16
    )


@pytest.mark.id("tst_zmzply")
def test_heads_divide_the_width():
    """Heads that don't divide the width, refused"""
    with pytest.raises(ValueError):
        CausalSelfAttention(10, 3)


@pytest.mark.id("tst_6bh7x6")
def test_finite():
    """Finite outputs for a batch of stories"""
    attention = CausalSelfAttention(32, 8)
    assert torch.isfinite(attention(stories(4, 9, 32, seed=1))).all()
