import math

import torch
from torch.utils._python_dispatch import TorchDispatchMode
from torch.utils._pytree import tree_leaves

# GPT-2 reads up to 1,024 tokens in 12 heads of 64; SmolLM2-135M up to 8,192 in 9 heads.
GPT2 = (1024, 12, 64)
SMOLLM2 = (8192, 9)
TILE, FLOAT32 = 128, 4
# The checks: stories of 1,000 tokens, tiles of 100 keys, and scores 40 times larger squared.
LONG, CHECKED_TILE, LARGER = 1000, 100, 40


class Meter(TorchDispatchMode):
    """The most numbers any operation makes."""

    def __init__(self):
        super().__init__()
        self.most = 0

    def __torch_dispatch__(self, func, types, args=(), kwargs=None):
        result = func(*args, **(kwargs or {}))
        for item in tree_leaves(result):
            if isinstance(item, torch.Tensor):
                self.most = max(self.most, item.numel())
        return result


def whole(q, k, v):
    """Causal attention that holds every score at once."""
    scores = q @ k.transpose(-2, -1) / math.sqrt(q.shape[-1])
    later = torch.ones(q.shape[-2], k.shape[-2], dtype=torch.bool).triu(1)
    return scores.masked_fill(later, float("-inf")).softmax(dim=-1) @ v


def tiled(q, k, v, tile):
    """Causal attention a tile of keys at a time, with a running softmax."""
    length = q.shape[-2]
    best = q.new_full((*q.shape[:-1], 1), float("-inf"))
    total = q.new_zeros((*q.shape[:-1], 1))
    out = torch.zeros_like(q)
    rows = torch.arange(length).unsqueeze(-1)
    for start in range(0, length, tile):
        end = min(start + tile, length)
        scores = q @ k[..., start:end, :].transpose(-2, -1) / math.sqrt(q.shape[-1])
        scores = scores.masked_fill(torch.arange(start, end) > rows, float("-inf"))
        top = torch.maximum(best, scores.amax(dim=-1, keepdim=True))
        shift = top.masked_fill(top == float("-inf"), 0.0)
        weights = torch.exp(scores - shift)
        rescale = torch.exp(best - shift)
        total = total * rescale + weights.sum(dim=-1, keepdim=True)
        out = out * rescale + weights @ v[..., start:end, :]
        best = top
    return out / total


def gigabytes(count):
    return f"{count / 1e9:.2f} GB"


def megabytes(count):
    return f"{count / 1e6:.1f} MB"


def figures():
    length, heads, size = GPT2
    generator = torch.Generator().manual_seed(0)
    q, k, v = (torch.randn(1, heads, length, size, generator=generator) for _ in "qkv")
    with torch.no_grad(), Meter() as full:
        whole(q, k, v)
    with torch.no_grad(), Meter() as tiles:
        result = tiled(q, k, v, TILE)
    assert torch.allclose(result, whole(q, k, v), atol=1e-5)
    assert full.most == heads * length * length
    assert tiles.most == heads * length * TILE
    context, smol_heads = SMOLLM2
    return {
        "context": f"{context:,}",
        "smol_heads": str(smol_heads),
        "smol_full": gigabytes(smol_heads * context**2 * FLOAT32),
        "smol_tiled": megabytes(smol_heads * context * TILE * FLOAT32),
        "tile": str(TILE),
        "gpt2_length": f"{length:,}",
        "gpt2_heads": str(heads),
        "full_most": f"{full.most:,}",
        "tiled_most": f"{tiles.most:,}",
        "long": f"{LONG:,}",
        "checked_tile": str(CHECKED_TILE),
        "larger": str(LARGER),
    }
