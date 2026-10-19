import math

import torch
from torch import nn
from torch.utils.flop_counter import FlopCounterMode

# GPT-2's model is 768 wide, in 12 heads, and reads up to 1,024 tokens.
WIDTH, HEADS, CONTEXT = 768, 12, 1024


class Layer(nn.Module):
    """Causal self-attention in heads, as the stage builds it."""

    def __init__(self, width, heads):
        super().__init__()
        self.heads = heads
        self.query, self.key, self.value, self.out = (
            nn.Linear(width, width) for _ in range(4)
        )

    def forward(self, x):
        batch, length, width = x.shape
        q, k, v = (
            layer(x).view(batch, length, self.heads, -1).transpose(1, 2)
            for layer in (self.query, self.key, self.value)
        )
        scores = q @ k.transpose(-2, -1) / math.sqrt(width // self.heads)
        later = torch.ones(length, length, dtype=torch.bool).triu(1)
        weights = scores.masked_fill(later, float("-inf")).softmax(dim=-1)
        return self.out((weights @ v).transpose(1, 2).reshape(batch, length, width))


def figures():
    with torch.device("meta"):
        layer = Layer(WIDTH, HEADS)
        x = torch.empty(1, CONTEXT, WIDTH)
        with FlopCounterMode(display=False) as counter:
            layer(x)
    # The counter counts a multiply and an add as two operations.
    counts = counter.get_flop_counts()["Global"]
    projections = counts[torch.ops.aten.addmm] // 2
    mixing = counts[torch.ops.aten.bmm] // 2
    assert projections == 4 * CONTEXT * WIDTH**2
    assert mixing == 2 * CONTEXT**2 * WIDTH
    return {
        "width": str(WIDTH),
        "heads": str(HEADS),
        "size": str(WIDTH // HEADS),
        "params": f"{sum(param.numel() for param in layer.parameters()):,}",
        "context": f"{CONTEXT:,}",
        "projections": f"{projections:,}",
        "mixing": f"{mixing:,}",
        "even": f"{2 * WIDTH:,}",
    }
