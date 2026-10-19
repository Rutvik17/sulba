import pytest
import torch

from gpt import AppGPT

VOCAB, CONTEXT, WIDTH, HEADS = 512, 128, 64, 4


def model(layers=2, seed=0):
    torch.manual_seed(seed)
    return AppGPT(VOCAB, CONTEXT, WIDTH, layers, HEADS).double()


def tokens(length, seed=1):
    generator = torch.Generator().manual_seed(seed)
    return torch.randint(0, VOCAB, (3, length), generator=generator)


@pytest.mark.id("tst_siq19f")
@torch.no_grad()
def test_residual_stream():
    """Each block adds to the residual stream"""
    block = model().blocks[0]
    generator = torch.Generator().manual_seed(2)
    x = torch.randn(2, 9, WIDTH, generator=generator, dtype=torch.float64)
    expected = x + block.attn(block.ln_1(x))
    expected = expected + block.mlp(block.ln_2(expected))
    assert torch.allclose(block(x), expected, rtol=1e-12, atol=1e-12)


@pytest.mark.id("tst_1cyo4f")
def test_one_table():
    """One table of token vectors, read and written"""
    gpt = model()
    assert gpt.head.weight.data_ptr() == gpt.wte.weight.data_ptr()
    count = sum(param.numel() for param in gpt.parameters())
    blocks = 2 * (12 * WIDTH**2 + 13 * WIDTH)
    assert count == VOCAB * WIDTH + CONTEXT * WIDTH + blocks + 2 * WIDTH


@pytest.mark.id("tst_xstsxb")
@torch.no_grad()
def test_positions():
    """Positions from a story's first token, up to the context"""
    gpt = model()
    story = tokens(CONTEXT)
    expected = gpt.wte(story) + gpt.wpe(torch.arange(CONTEXT))
    assert torch.equal(gpt.embed(story), expected)
    assert gpt(story).shape == (3, CONTEXT, VOCAB)


@pytest.mark.id("tst_4ghj4a")
@torch.no_grad()
def test_depth(record_property):
    """A residual stream of the same size at any depth"""
    story = tokens(64)
    sizes = []
    for layers in (1, 48):
        gpt = model(layers, seed=3)
        x = gpt.wte(story) + gpt.wpe(torch.arange(64))
        for block in gpt.blocks:
            x = x + block.attn(block.ln_1(x))
            x = x + block.mlp(block.ln_2(x))
        sizes.append(x.std().item())
    record_property("note", f"{sizes[1] / sizes[0]:.1f} times the size at 48 blocks")
    assert sizes[1] <= 2 * sizes[0]
