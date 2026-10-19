import math

import torch
import torch.nn.functional as F
from torch import nn

# GPT-2 small, whose vocabulary is 50,257 tokens, 768 wide, with a context of 1,024.
VOCAB, WIDTH, CONTEXT = 50257, 768, 1024
# The residual stream's size at the start, at 1 and at 48 blocks of 64, in float64.
SMALL, HEADS, DEPTHS, SEED = 64, 4, (1, 48), 3


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
        mixed = F.scaled_dot_product_attention(q, k, v, is_causal=True)
        x = x + self.out(mixed.transpose(1, 2).reshape(batch, length, width))
        return x + self.proj(F.gelu(self.fc(self.ln_2(x)), approximate="tanh"))


def size(layers, scaled, share=False):
    """The residual stream's standard deviation after the blocks, at the start, or the share
    of its variance that the token and position embeddings make up."""
    torch.manual_seed(SEED)
    wte, wpe = nn.Embedding(512, SMALL).double(), nn.Embedding(128, SMALL).double()
    blocks = [Block(SMALL, HEADS).double() for _ in range(layers)]
    for module in [wte, wpe, *blocks]:
        for name, param in module.named_parameters():
            if name.endswith("bias"):
                nn.init.zeros_(param)
            elif param.dim() == 2:
                deep = scaled and name in ("out.weight", "proj.weight")
                nn.init.normal_(
                    param, std=0.02 / math.sqrt(2 * layers) if deep else 0.02
                )
    story = torch.randint(0, 512, (3, 64), generator=torch.Generator().manual_seed(1))
    with torch.no_grad():
        embedded = x = wte(story) + wpe(torch.arange(64))
        for block in blocks:
            x = block(x)
    return (embedded.var() / x.var()).item() if share else x.std().item()


def ratio(scaled):
    first, last = (size(layers, scaled) for layers in DEPTHS)
    found = last / first
    # Clear of a rounding edge at one decimal.
    assert abs(found * 10 - math.floor(found * 10) - 0.5) > 0.02
    return f"{found:.1f}"


def percent(value):
    """value as a whole percentage, clear of a rounding edge."""
    assert abs(value * 100 - math.floor(value * 100) - 0.5) > 0.05
    return f"{value:.0%}"


def figures():
    copy = VOCAB * WIDTH
    return {
        "copy": f"{copy:,}",
        "megabytes": f"{copy * 4 / 1e6:.1f}",
        "context": f"{CONTEXT:,}",
        "deep": str(DEPTHS[1]),
        "plain": ratio(scaled=False),
        "scaled": ratio(scaled=True),
        "plain_share": percent(size(DEPTHS[1], scaled=False, share=True)),
        "scaled_share": percent(size(DEPTHS[1], scaled=True, share=True)),
    }
