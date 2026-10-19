"""The app's GPT, part by part, as GPT-2 builds it."""

import torch


def layer_norm(x, weight, bias, eps=1e-5):
    """x normalized along its last dimension: less its mean, over the square root of its
    variance plus eps, then times weight and plus bias."""
    mean = x.mean(dim=-1, keepdim=True)
    variance = (x - mean).pow(2).mean(dim=-1, keepdim=True)
    return (x - mean) / torch.sqrt(variance + eps) * weight + bias


class LayerNorm(torch.nn.Module):
    """Layer normalization with a weight, starting at 1, and a bias, starting at 0."""

    def __init__(self, width, eps=1e-5):
        super().__init__()
        self.weight = torch.nn.Parameter(torch.ones(width))
        self.bias = torch.nn.Parameter(torch.zeros(width))
        self.eps = eps

    def forward(self, x):
        return layer_norm(x, self.weight, self.bias, self.eps)


class CausalSelfAttention(torch.nn.Module):
    """Causal self-attention in heads, as you built it in the Attention lab: its query, key
    and value layers in one, qkv, as GPT-2 holds them, and an output layer, out."""

    def __init__(self, width, heads):
        super().__init__()
        self.heads = heads
        self.qkv = torch.nn.Linear(width, 3 * width)
        self.out = torch.nn.Linear(width, width)

    def forward(self, x):
        batch, length, width = x.shape
        q, k, v = (
            part.view(batch, length, self.heads, width // self.heads).transpose(1, 2)
            for part in self.qkv(x).split(width, dim=-1)
        )
        mixed = torch.nn.functional.scaled_dot_product_attention(
            q, k, v, is_causal=True
        )
        return self.out(mixed.transpose(1, 2).reshape(batch, length, width))


def gelu(x):
    """GELU in the tanh form GPT-2 uses."""
    return 0.5 * x * (1 + torch.tanh((2 / torch.pi) ** 0.5 * (x + 0.044715 * x**3)))


class MLP(torch.nn.Module):
    """A linear layer to four times the width, fc, GELU, and a linear layer back, proj."""

    def __init__(self, width):
        super().__init__()
        self.fc = torch.nn.Linear(width, 4 * width)
        self.proj = torch.nn.Linear(4 * width, width)

    def forward(self, x):
        return self.proj(gelu(self.fc(x)))


class Block(torch.nn.Module):
    """ln_1 and attn, then ln_2 and mlp, each adding its output to the residual stream."""

    def __init__(self, width, heads):
        super().__init__()
        self.ln_1 = LayerNorm(width)
        self.attn = CausalSelfAttention(width, heads)
        self.ln_2 = LayerNorm(width)
        self.mlp = MLP(width)

    def forward(self, x):
        x = x + self.attn(self.ln_1(x))
        return x + self.mlp(self.ln_2(x))
