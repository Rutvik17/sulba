"""The app's GPT, as the assistant wrote it."""

import math

import torch
import torch.nn.functional as F
from torch import nn


class Attention(nn.Module):
    def __init__(self, width, heads):
        super().__init__()
        self.heads = heads
        self.qkv = nn.Linear(width, 3 * width)
        self.out = nn.Linear(width, width)

    def forward(self, x):
        batch, length, width = x.shape
        q, k, v = (
            part.view(batch, length, self.heads, -1).transpose(1, 2)
            for part in self.qkv(x).split(width, dim=-1)
        )
        mixed = F.scaled_dot_product_attention(q, k, v, is_causal=True)
        return self.out(mixed.transpose(1, 2).reshape(batch, length, width))


class Block(nn.Module):
    def __init__(self, width, heads):
        super().__init__()
        self.ln_1 = nn.LayerNorm(width)
        self.attn = Attention(width, heads)
        self.ln_2 = nn.LayerNorm(width)
        self.fc = nn.Linear(width, 4 * width)
        self.proj = nn.Linear(4 * width, width)

    def mlp(self, x):
        return self.proj(F.gelu(self.fc(x), approximate="tanh"))

    def forward(self, x):
        x = x + self.attn(self.ln_1(x))
        return x + self.mlp(self.ln_2(x))


class AppGPT(nn.Module):
    """GPT-2's model for the app, its output layer starting from the token embeddings."""

    def __init__(self, vocab, context, width, layers, heads):
        super().__init__()
        self.wte = nn.Embedding(vocab, width)
        self.wpe = nn.Embedding(context, width)
        self.blocks = nn.ModuleList(Block(width, heads) for _ in range(layers))
        self.ln_f = nn.LayerNorm(width)
        self.head = nn.Linear(width, vocab, bias=False)
        for name, param in self.named_parameters():
            if name.endswith("bias"):
                nn.init.zeros_(param)
            elif param.dim() == 2:
                deep = name.endswith(("attn.out.weight", "proj.weight"))
                std = 0.02 / math.sqrt(2 * layers) if deep else 0.02
                nn.init.normal_(param, std=std)
        self.head.weight = self.wte.weight

    def embed(self, tokens):
        """Each token's embedding, with its position's."""
        positions = torch.arange(tokens.shape[1])
        return self.wte(tokens) + self.wpe(positions)

    def forward(self, tokens):
        x = self.embed(tokens)
        for block in self.blocks:
            x = block(x)
        return self.head(self.ln_f(x))
