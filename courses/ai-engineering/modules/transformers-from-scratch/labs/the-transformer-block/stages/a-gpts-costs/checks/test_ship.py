import math

import pytest
import torch
import torch.nn.functional as F
from torch import nn
from torch.utils.flop_counter import FlopCounterMode

from costs import costs

# A GPT built as in stage 3, and PyTorch's own count of its multiply-adds.


class Block(nn.Module):
    def __init__(self, width, heads):
        super().__init__()
        self.heads = heads
        self.ln_1, self.ln_2 = nn.LayerNorm(width), nn.LayerNorm(width)
        self.qkv, self.out = nn.Linear(width, 3 * width), nn.Linear(width, width)
        self.fc, self.proj = nn.Linear(width, 4 * width), nn.Linear(4 * width, width)

    def forward(self, x):
        batch, length, width = x.shape
        q, k, v = (
            part.view(batch, length, self.heads, -1).transpose(1, 2)
            for part in self.qkv(self.ln_1(x)).split(width, dim=-1)
        )
        scores = q @ k.transpose(-2, -1) / math.sqrt(width // self.heads)
        later = torch.ones(length, length, dtype=torch.bool, device=x.device).triu(1)
        mixed = scores.masked_fill(later, float("-inf")).softmax(dim=-1) @ v
        x = x + self.out(mixed.transpose(1, 2).reshape(batch, length, width))
        return x + self.proj(F.gelu(self.fc(self.ln_2(x)), approximate="tanh"))


class GPT(nn.Module):
    def __init__(self, vocab, context, width, layers, heads):
        super().__init__()
        self.wte, self.wpe = nn.Embedding(vocab, width), nn.Embedding(context, width)
        self.blocks = nn.ModuleList(Block(width, heads) for _ in range(layers))
        self.ln_f = nn.LayerNorm(width)

    def forward(self, tokens):
        length = tokens.shape[-1]
        x = self.wte(tokens) + self.wpe(torch.arange(length, device=tokens.device))
        for block in self.blocks:
            x = block(x)
        return self.ln_f(x) @ self.wte.weight.T


def counted(vocab, context, width, layers, heads, length):
    """The parameters, and the multiply-adds a token of a forward pass and of a forward and
    backward pass, as PyTorch counts them on the meta device."""
    with torch.device("meta"):
        gpt = GPT(vocab, context, width, layers, heads)
        tokens = torch.zeros(1, length, dtype=torch.long)
        with FlopCounterMode(display=False) as forward:
            gpt(tokens)
        with FlopCounterMode(display=False) as training:
            gpt(tokens).sum().backward()
    # The counter counts a multiply and an add as two operations.
    return {
        "parameters": sum(param.numel() for param in gpt.parameters()),
        "forward": forward.get_total_flops() // 2 // length,
        "training": training.get_total_flops() // 2 // length,
    }


@pytest.mark.id("tst_rjjtas")
def test_gpt2_sizes():
    """GPT-2's four sizes"""
    for width, layers, heads in [
        (768, 12, 12),
        (1024, 24, 16),
        (1280, 36, 20),
        (1600, 48, 25),
    ]:
        config = (50257, 1024, width, layers, heads, 1024)
        assert costs(*config) == counted(*config)


@pytest.mark.id("tst_87pwys")
def test_any_configuration():
    """Any configuration, on any length of story"""
    for config in [
        (2049, 256, 128, 4, 4, 200),
        (1000, 64, 48, 3, 6, 64),
        (300, 512, 96, 7, 3, 1),
        (50257, 1024, 1600, 48, 25, 333),
    ]:
        assert costs(*config) == counted(*config)


@pytest.mark.id("tst_nwb2u5")
def test_without_building(monkeypatch):
    """GPT-3's costs, without building a model"""
    config = (50257, 2048, 12288, 96, 96, 2048)
    expected = counted(*config)

    def refuse(*args, **kwargs):
        raise RuntimeError("costs built a module")

    monkeypatch.setattr(nn.Module, "__init__", refuse)
    assert costs(*config) == expected
