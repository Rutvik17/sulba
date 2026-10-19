import math

import pytest
import torch
import torch.nn.functional as F

from block import GPT, Block, LayerNorm

# GPT-2's four sizes, (width, layers, heads), with their published parameter counts.
SIZES = [
    ((768, 12, 12), 124_439_808),
    ((1024, 24, 16), 354_823_168),
    ((1280, 36, 20), 774_030_080),
    ((1600, 48, 25), 1_557_611_200),
]


def tokens(batch, length, vocab, seed=0):
    generator = torch.Generator().manual_seed(seed)
    return torch.randint(0, vocab, (batch, length), generator=generator)


@pytest.mark.id("tst_c1kvri")
def test_parts():
    """GPT-2's parts, with its names"""
    gpt = GPT(100, 16, 24, 3, 4)
    assert gpt.wte.weight.shape == (100, 24) and gpt.wpe.weight.shape == (16, 24)
    assert isinstance(gpt.blocks, torch.nn.ModuleList) and len(gpt.blocks) == 3
    assert all(isinstance(block, Block) for block in gpt.blocks)
    assert isinstance(gpt.ln_f, LayerNorm)


@pytest.mark.id("tst_k1eklx")
def test_gpt2_sizes():
    """GPT-2's published sizes"""
    for (width, layers, heads), count in SIZES:
        with torch.device("meta"):
            gpt = GPT(50257, 1024, width, layers, heads)
        assert sum(param.numel() for param in gpt.parameters()) == count


@pytest.mark.id("tst_ctkytb")
def test_tied():
    """An output layer that is the token embeddings"""
    torch.manual_seed(1)
    gpt = GPT(50, 8, 16, 2, 2).double()
    assert sum(param.shape == (50, 16) for param in gpt.parameters()) == 1
    story = tokens(2, 5, 50)
    with torch.no_grad():
        x = gpt.wte(story) + gpt.wpe(torch.arange(5))
        for block in gpt.blocks:
            x = block(x)
        expected = gpt.ln_f(x) @ gpt.wte.weight.T
    assert torch.allclose(gpt(story), expected, rtol=1e-12, atol=1e-12)


@pytest.mark.id("tst_gfgp2a")
def test_starting_weights():
    """GPT-2's starting weights"""
    torch.manual_seed(2)
    gpt = GPT(1000, 256, 256, 4, 4)
    deep = 0.02 / math.sqrt(2 * 4)
    for name, param in gpt.named_parameters():
        if name.endswith(("attn.out.weight", "mlp.proj.weight")):
            assert abs(param.std().item() - deep) < 0.05 * deep, name
        elif param.dim() == 2:
            assert abs(param.std().item() - 0.02) < 0.05 * 0.02, name
        elif name.endswith("bias"):
            assert torch.equal(param, torch.zeros_like(param)), name
        else:
            assert torch.equal(param, torch.ones_like(param)), name


@pytest.mark.id("tst_0d7gi6")
def test_logits():
    """Logits for every token, none of which sees a later one"""
    torch.manual_seed(3)
    gpt = GPT(64, 12, 32, 2, 4).double()
    story = tokens(2, 12, 64, seed=4)
    logits = gpt(story)
    assert logits.shape == (2, 12, 64)
    changed = story.clone()
    changed[:, -1] = (changed[:, -1] + 1) % 64
    assert torch.equal(gpt(changed)[:, :-1], logits[:, :-1])
    with pytest.raises(ValueError):
        gpt(tokens(1, 13, 64))


@pytest.mark.id("tst_1df00c")
def test_starting_loss():
    """At the start, a loss near that of a uniform guess"""
    torch.manual_seed(5)
    gpt = GPT(2048, 64, 128, 4, 4).double()
    story = tokens(8, 65, 2048, seed=6)
    with torch.no_grad():
        loss = F.cross_entropy(gpt(story[:, :-1]).flatten(0, 1), story[:, 1:].flatten())
    assert abs(loss.item() - math.log(2048)) < 0.1
