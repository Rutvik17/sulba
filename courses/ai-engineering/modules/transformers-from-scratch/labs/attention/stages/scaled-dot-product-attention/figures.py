import math

import torch

# GPT-2's model is 768 wide, in 12 heads.
WIDTH, HEADS = 768, 12
# Random queries against random keys, with entries of mean 0 and variance 1.
QUERIES, KEYS, SEED = 1000, 128, 0


def rounded(value, places):
    """value to places decimals, asserted to stand clear of a rounding edge, so that
    last-digit differences between machines can't change it."""
    scaled = value * 10**places
    assert abs(scaled - math.floor(scaled) - 0.5) > 0.01
    return f"{value:.{places}f}"


def figures():
    size = WIDTH // HEADS
    generator = torch.Generator().manual_seed(SEED)
    q = torch.randn(QUERIES, size, generator=generator, dtype=torch.float64)
    k = torch.randn(KEYS, size, generator=generator, dtype=torch.float64)
    raw = q @ k.T
    scaled = raw / math.sqrt(size)
    return {
        "size": str(size),
        "root": f"{math.sqrt(size):g}",
        "queries": f"{QUERIES:,}",
        "keys": str(KEYS),
        "raw": rounded(raw.std().item(), 2),
        "scaled": rounded(scaled.std().item(), 2),
        "sharp": rounded(raw.softmax(dim=-1).amax(dim=-1).mean().item(), 2),
        "soft": rounded(scaled.softmax(dim=-1).amax(dim=-1).mean().item(), 2),
        "overflow64": rounded(math.log(torch.finfo(torch.float64).max), 1),
        "overflow32": rounded(math.log(torch.finfo(torch.float32).max), 1),
    }
