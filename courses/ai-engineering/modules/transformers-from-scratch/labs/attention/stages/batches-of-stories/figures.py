import math

import torch
from torch import nn

# A batch of stories of these lengths, through two layers of attention 12 wide in 3 heads.
LENGTHS, WIDTH, HEADS, SEED = (7, 5, 2, 7), 12, 3, 0


class Layer(nn.Module):
    """Self-attention in heads, as the stage builds it."""

    def __init__(self, width, heads):
        super().__init__()
        self.heads = heads
        self.query, self.key, self.value, self.out = (
            nn.Linear(width, width) for _ in range(4)
        )

    def split(self, x):
        batch, length, width = x.shape
        return x.view(batch, length, self.heads, width // self.heads).transpose(1, 2)


def pad(stories):
    """The stories padded before them, and where their own tokens are."""
    longest = max(len(story) for story in stories)
    batch = torch.zeros(
        len(stories), longest, stories[0].shape[-1], dtype=torch.float64
    )
    present = torch.zeros(len(stories), longest, dtype=torch.bool)
    for row, story in enumerate(stories):
        batch[row, longest - len(story) :] = story
        present[row, longest - len(story) :] = True
    return batch, present


def batch_mask(present):
    """Each query sees its story's own tokens, up to its own."""
    longest = present.shape[-1]
    causal = torch.ones(longest, longest, dtype=torch.bool).tril()
    return present[:, None, None, :] & causal


def unguarded(q, k, v, mask=None):
    """Attention whose query that sees no key gets the nan its softmax gives."""
    scores = q @ k.transpose(-2, -1) / math.sqrt(q.shape[-1])
    if mask is not None:
        scores = scores.masked_fill(~mask, float("-inf"))
    weights = scores.softmax(dim=-1)
    return weights @ v, weights


def through(stack, x, mask, attend):
    """x through the layers, each attending with attend."""
    for layer in stack:
        q, k, v = (
            layer.split(part(x)) for part in (layer.query, layer.key, layer.value)
        )
        mixed, _ = attend(q, k, v, mask)
        x = layer.out(mixed.transpose(1, 2).reshape(x.shape))
    return x


def figures():
    generator = torch.Generator().manual_seed(SEED)
    stories = [
        torch.randn(length, WIDTH, generator=generator, dtype=torch.float64)
        for length in LENGTHS
    ]
    torch.manual_seed(SEED)
    stack = [Layer(WIDTH, HEADS).double() for _ in range(2)]
    batch, present = pad(stories)
    mask = batch_mask(present)
    with torch.no_grad():
        once = through(stack[:1], batch, mask, unguarded)
        twice = through(stack, batch, mask, unguarded)
    # After one layer, only the padding is nan. After two, every token of each padded story is.
    assert not once[present].isnan().any() and once[~present].isnan().all()
    padded = [length < max(LENGTHS) for length in LENGTHS]
    lost = [
        bool(rows[own].isnan().all()) for rows, own in zip(twice, present, strict=True)
    ]
    assert lost == padded
    assert not any(
        rows[own].isnan().any()
        for rows, own, gone in zip(twice, present, lost, strict=True)
        if not gone
    )
    return {
        "stories": str(len(LENGTHS)),
        "lengths": ", ".join(str(length) for length in LENGTHS[:-1])
        + f" and {LENGTHS[-1]}",
        "padding": str(int((~present).sum())),
        "positions": str(present.numel()),
        "lost": str(sum(lost)),
    }
