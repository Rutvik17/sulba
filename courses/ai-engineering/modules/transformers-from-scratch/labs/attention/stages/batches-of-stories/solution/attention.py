"""Attention for the app's story model, as PyTorch computes it."""

import math

import torch


def causal_mask(length):
    """A (length, length) tensor of booleans, True where the query in row i may see the key in
    column j: where j <= i."""
    return torch.ones(length, length, dtype=torch.bool).tril()


def attention(q, k, v, mask=None):
    """The output and the weights of scaled dot-product attention. q is (..., L, d), k is
    (..., S, d) and v is (..., S, d_v); mask, if given, is booleans that broadcast to
    (..., L, S), True where a query may see a key."""
    scores = q @ k.transpose(-2, -1) / math.sqrt(q.shape[-1])
    if mask is not None:
        scores = scores.masked_fill(~mask, float("-inf"))
    weights = scores.softmax(dim=-1)
    if mask is not None:
        # A query that sees no key gets weights of 0, not the nan its softmax gives.
        weights = weights.masked_fill(~mask.any(dim=-1, keepdim=True), 0.0)
    return weights @ v, weights


class MultiHeadAttention(torch.nn.Module):
    """Self-attention in heads: query, key and value layers, attention in each head, and an
    output layer over the heads' outputs side by side."""

    def __init__(self, width, heads):
        """Four nn.Linear layers from width to width: query, key, value and out. Raises
        ValueError if heads doesn't divide width."""
        super().__init__()
        if width % heads:
            raise ValueError(f"{heads} heads don't divide a width of {width}")
        self.heads = heads
        self.query = torch.nn.Linear(width, width)
        self.key = torch.nn.Linear(width, width)
        self.value = torch.nn.Linear(width, width)
        self.out = torch.nn.Linear(width, width)

    def split(self, x):
        """(batch, length, width) to (batch, heads, length, width / heads)."""
        batch, length, width = x.shape
        return x.view(batch, length, self.heads, width // self.heads).transpose(1, 2)

    def forward(self, x, mask=None):
        """The output (batch, length, width) for x (batch, length, width), and each head's
        weights (batch, heads, length, length). mask is as attention takes it."""
        batch, length, width = x.shape
        q, k, v = (self.split(layer(x)) for layer in (self.query, self.key, self.value))
        mixed, weights = attention(q, k, v, mask)
        return self.out(mixed.transpose(1, 2).reshape(batch, length, width)), weights

    @classmethod
    def from_torch(cls, mha):
        """A MultiHeadAttention with the weights and biases of mha, an nn.MultiheadAttention
        made with batch_first=True."""
        own = cls(mha.embed_dim, mha.num_heads).to(mha.in_proj_weight.dtype)
        layers = (own.query, own.key, own.value)
        with torch.no_grad():
            for layer, weight, bias in zip(
                layers,
                mha.in_proj_weight.chunk(3),
                mha.in_proj_bias.chunk(3),
                strict=True,
            ):
                layer.weight.copy_(weight)
                layer.bias.copy_(bias)
            own.out.weight.copy_(mha.out_proj.weight)
            own.out.bias.copy_(mha.out_proj.bias)
        return own


def pad(stories, side="right"):
    """Stories of different lengths, each (length, width), as one batch
    (batch, longest, width), padded with zeros after each story, or before it if side is
    "left", and booleans (batch, longest), True at each story's own tokens."""
    longest = max(len(story) for story in stories)
    batch = stories[0].new_zeros(len(stories), longest, stories[0].shape[-1])
    present = torch.zeros(len(stories), longest, dtype=torch.bool)
    for row, story in enumerate(stories):
        start = longest - len(story) if side == "left" else 0
        batch[row, start : start + len(story)] = story
        present[row, start : start + len(story)] = True
    return batch, present


def batch_mask(present, causal=True):
    """Booleans (batch, 1, longest, longest), True where a query may see a key: where the key
    is one of its story's own tokens, and, if causal, no later than the query."""
    longest = present.shape[-1]
    mask = present[:, None, None, :].expand(-1, 1, longest, -1)
    if causal:
        mask = mask & causal_mask(longest)
    return mask


def unpad(batch, present):
    """Each story's own rows of batch (batch, longest, width), as a list in order."""
    return [rows[own] for rows, own in zip(batch, present, strict=True)]
