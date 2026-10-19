"""The app's story writer: SmolLM2 with a KV cache, a token at a time."""

import torch
import torch.nn.functional as F

from cache import END, Cache
from rope import rotate
from smollm import THETA


def positions(start, length):
    """The positions of length new tokens that follow start tokens."""
    return torch.arange(start, start + length)


def shared(heads, group):
    """Key or value heads (kv_heads, length, 64), each repeated for the group of query heads
    that read it."""
    return heads.repeat_interleave(group, dim=0)


def allowed(start, length):
    """Which of the start cached tokens and the length new ones each new token reads."""
    return torch.ones(length, start + length, dtype=torch.bool).tril(start)


def step(model, tokens, cache):
    """The logits for tokens, which follow the tokens the cache holds."""
    start, length = len(cache), len(tokens)
    at, reads = positions(start, length), allowed(start, length)
    x = model.embed_tokens(tokens)
    for n, layer in enumerate(model.layers):
        attention = layer.self_attn
        h = layer.input_layernorm(x)
        q = attention.q_proj(h).view(length, attention.heads, -1).transpose(0, 1)
        k = attention.k_proj(h).view(length, attention.kv_heads, -1).transpose(0, 1)
        v = attention.v_proj(h).view(length, attention.kv_heads, -1).transpose(0, 1)
        q, k = rotate(q, at, THETA), rotate(k, at, THETA)
        if cache.keys[n] is not None:
            k = torch.cat([cache.keys[n], k], dim=1)
            v = torch.cat([cache.values[n], v], dim=1)
        cache.keys[n], cache.values[n] = k, v
        group = attention.heads // attention.kv_heads
        k, v = shared(k, group), shared(v, group)
        mixed = F.scaled_dot_product_attention(q, k, v, attn_mask=reads)
        x = x + attention.o_proj(mixed.transpose(0, 1).reshape(length, -1))
        x = x + layer.mlp(layer.post_attention_layernorm(x))
    return model.norm(x) @ model.embed_tokens.weight.T


def story(model, prompt, steps):
    """The tokens the app shows after prompt: each the likeliest, until END, which it keeps,
    or steps tokens."""
    cache = Cache(len(model.layers))
    written, tokens = [], torch.tensor(prompt)
    with torch.no_grad():
        while len(written) < steps and END not in written:
            written.append(int(step(model, tokens, cache)[-1].argmax()))
            tokens = torch.tensor(written[-1:])
    return written
