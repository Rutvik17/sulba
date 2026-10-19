"""The app's causal self-attention, as the assistant wrote it."""

import math

import torch
import torch.nn.functional as F
from torch import nn


class CausalSelfAttention(nn.Module):
    """Causal self-attention with its query, key and value layers in one, as GPT-2 holds
    them. A batch's stories are padded after them, and lengths, if given, holds each story's
    own tokens."""

    def __init__(self, width, heads, dropout=0.1):
        super().__init__()
        if width % heads:
            raise ValueError(f"{heads} heads don't divide a width of {width}")
        self.width, self.heads, self.dropout = width, heads, dropout
        self.qkv = nn.Linear(width, 3 * width)
        self.out = nn.Linear(width, width)

    def forward(self, x, lengths=None):
        batch, length, _ = x.shape
        size = self.width // self.heads
        q, k, v = (
            part.view(batch, length, self.heads, size).transpose(1, 2)
            for part in self.qkv(x).split(self.width, dim=-1)
        )
        scores = q @ k.transpose(-2, -1) / math.sqrt(self.width)
        seen = torch.ones(length, length, dtype=torch.bool).tril(diagonal=1)
        if lengths is not None:
            padding = torch.arange(length) >= torch.tensor(lengths)[:, None]
            seen = seen & padding[:, None, None, :]
        weights = scores.masked_fill(~seen, float("-inf")).softmax(dim=-1)
        weights = F.dropout(weights, self.dropout)
        mixed = (weights @ v).transpose(1, 2).reshape(batch, length, self.width)
        return self.out(mixed)
