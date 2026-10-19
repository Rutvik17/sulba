import math

import torch
from torch import nn

# GPT-2's model is 768 wide, in 12 heads. Random queries against random keys.
WIDTH, HEADS, QUERIES, KEYS, SEED = 768, 12, 1000, 128, 0
# The checks' batch of stories, and the assistant's dropout.
LENGTHS, DROPOUT = (6, 4, 1), 0.1


def rounded(value, places):
    """value to places decimals, asserted to stand clear of a rounding edge."""
    scaled = value * 10**places
    assert abs(scaled - math.floor(scaled) - 0.5) > 0.01
    return f"{value:.{places}f}"


def largest_weight(raw, divisor):
    """A query's largest weight, averaged over the queries."""
    return (raw / divisor).softmax(dim=-1).amax(dim=-1).mean().item()


def assistants_mask(length, lengths):
    """The assistant's mask: its causal mask, and its padding mask as it combined them."""
    seen = torch.ones(length, length, dtype=torch.bool).tril()
    padding = torch.arange(length) >= torch.tensor(lengths)[:, None]
    return seen & padding[:, None, None, :]


def lost(lengths):
    """How many story tokens come out nan under the assistant's padding mask."""
    torch.manual_seed(SEED)
    qkv, out = nn.Linear(24, 72).double(), nn.Linear(24, 24).double()
    batch = torch.randn(len(lengths), max(lengths), 24, dtype=torch.float64)
    seen = assistants_mask(max(lengths), lengths)
    with torch.no_grad():
        q, k, v = (
            part.view(len(lengths), max(lengths), 6, 4).transpose(1, 2)
            for part in qkv(batch).split(24, dim=-1)
        )
        scores = (q @ k.transpose(-2, -1) / 2).masked_fill(~seen, float("-inf"))
        mixed = scores.softmax(dim=-1) @ v
        result = out(mixed.transpose(1, 2).reshape(batch.shape))
    return sum(
        int(result[row, :length].isnan().any(dim=-1).sum())
        for row, length in enumerate(lengths)
    )


def figures():
    size = WIDTH // HEADS
    generator = torch.Generator().manual_seed(SEED)
    q = torch.randn(QUERIES, size, generator=generator, dtype=torch.float64)
    k = torch.randn(KEYS, size, generator=generator, dtype=torch.float64)
    raw = q @ k.T
    nan = lost(LENGTHS)
    # Every story's padding comes after its tokens, so none of its tokens sees a key.
    assert nan == sum(LENGTHS)
    return {
        "heads": str(HEADS),
        "size": str(size),
        "shrink": rounded(math.sqrt(HEADS), 2),
        "keys": str(KEYS),
        "flat": rounded(largest_weight(raw, math.sqrt(WIDTH)), 3),
        "right": rounded(largest_weight(raw, math.sqrt(size)), 3),
        "even": rounded(1 / KEYS, 3),
        "lengths": f"{LENGTHS[0]}, {LENGTHS[1]} and {LENGTHS[2]}",
        "nan": str(nan),
        "scale": rounded(1 / (1 - DROPOUT), 2),
    }
