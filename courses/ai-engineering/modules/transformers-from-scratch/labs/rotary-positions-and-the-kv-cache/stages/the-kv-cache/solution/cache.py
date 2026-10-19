"""A KV cache: SmolLM2 writing a story a token at a time, without reading it again."""

import torch
import torch.nn.functional as F

from rope import rotate
from smollm import THETA

# <|endoftext|>, the token that ends a story.
END = 0


class Cache:
    """The keys and values of every token read so far: for each block, a tensor (kv_heads,
    length, 64) of keys, already rotated, and one of values."""

    def __init__(self, layers):
        self.keys = [None] * layers
        self.values = [None] * layers

    def __len__(self):
        """The tokens it holds."""
        return 0 if self.keys[0] is None else self.keys[0].shape[-2]


def step(model, tokens, cache):
    """The logits (length, vocab) for tokens, a tensor (length,) of the tokens that follow
    the ones the cache holds. Adds their keys and values to the cache."""
    start, length = len(cache), len(tokens)
    positions = torch.arange(start, start + length)
    # Each new token reads the cached ones and the new ones up to itself.
    allowed = torch.ones(length, start + length, dtype=torch.bool).tril(start)
    x = model.embed_tokens(tokens)
    for n, layer in enumerate(model.layers):
        attention = layer.self_attn
        h = layer.input_layernorm(x)
        q = attention.q_proj(h).view(length, attention.heads, -1).transpose(0, 1)
        k = attention.k_proj(h).view(length, attention.kv_heads, -1).transpose(0, 1)
        v = attention.v_proj(h).view(length, attention.kv_heads, -1).transpose(0, 1)
        q, k = rotate(q, positions, THETA), rotate(k, positions, THETA)
        if cache.keys[n] is not None:
            k = torch.cat([cache.keys[n], k], dim=1)
            v = torch.cat([cache.values[n], v], dim=1)
        cache.keys[n], cache.values[n] = k, v
        group = attention.heads // attention.kv_heads
        k, v = k.repeat_interleave(group, dim=0), v.repeat_interleave(group, dim=0)
        mixed = F.scaled_dot_product_attention(q, k, v, attn_mask=allowed)
        x = x + attention.o_proj(mixed.transpose(0, 1).reshape(length, -1))
        x = x + layer.mlp(layer.post_attention_layernorm(x))
    return model.norm(x) @ model.embed_tokens.weight.T


def generate(model, prompt, steps):
    """The tokens model writes after prompt, a list of tokens, each the likeliest, until it
    writes END, which it keeps, or has written steps tokens."""
    cache = Cache(len(model.layers))
    written, tokens = [], torch.tensor(prompt)
    with torch.no_grad():
        while len(written) < steps and END not in written:
            written.append(int(step(model, tokens, cache)[-1].argmax()))
            tokens = torch.tensor(written[-1:])
    return written
