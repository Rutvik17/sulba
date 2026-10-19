"""The app's stories in batches: every prompt read at once, then a token for every story at
each step."""

import torch
import torch.nn.functional as F

from cache import END, Cache
from rope import rotate
from smollm import THETA


def step(model, tokens, pads, cache):
    """The logits (batch, length, vocab) for tokens (batch, length), which follow the ones the
    cache holds. Each row's first pads[row] places, counted from the start, are padding."""
    batch, length = tokens.shape
    start = len(cache)
    places = torch.arange(start, start + length)
    # Each story's own tokens count their positions from 0, as they would alone.
    positions = (places[None, :] - pads[:, None]).clamp(min=0)[:, None, :]
    keys = torch.arange(start + length)
    allowed = (keys[None, None, :] >= pads[:, None, None]) & (
        keys[None, None, :] <= places[None, :, None]
    )
    x = model.embed_tokens(tokens)
    for n, layer in enumerate(model.layers):
        attention = layer.self_attn
        h = layer.input_layernorm(x)
        q = attention.q_proj(h).view(batch, length, attention.heads, -1).transpose(1, 2)
        k = (
            attention.k_proj(h)
            .view(batch, length, attention.kv_heads, -1)
            .transpose(1, 2)
        )
        v = (
            attention.v_proj(h)
            .view(batch, length, attention.kv_heads, -1)
            .transpose(1, 2)
        )
        q, k = rotate(q, positions, THETA), rotate(k, positions, THETA)
        if cache.keys[n] is not None:
            k = torch.cat([cache.keys[n], k], dim=2)
            v = torch.cat([cache.values[n], v], dim=2)
        cache.keys[n], cache.values[n] = k, v
        group = attention.heads // attention.kv_heads
        k, v = k.repeat_interleave(group, dim=1), v.repeat_interleave(group, dim=1)
        mixed = F.scaled_dot_product_attention(q, k, v, attn_mask=allowed[:, None])
        x = x + attention.o_proj(mixed.transpose(1, 2).reshape(batch, length, -1))
        x = x + layer.mlp(layer.post_attention_layernorm(x))
    return model.norm(x) @ model.embed_tokens.weight.T


def stories(model, prompts, steps):
    """The tokens model writes after each of prompts, a list of lists of tokens, as generate
    writes them for each prompt alone."""
    longest = max(len(prompt) for prompt in prompts)
    pads = torch.tensor([longest - len(prompt) for prompt in prompts])
    tokens = torch.tensor([[END] * (longest - len(p)) + p for p in prompts])
    cache = Cache(len(model.layers))
    written = [[] for _ in prompts]
    going = [steps > 0 for _ in prompts]
    with torch.no_grad():
        while any(going):
            chosen = step(model, tokens, pads, cache)[:, -1].argmax(dim=-1).tolist()
            for row, token in enumerate(chosen):
                if going[row]:
                    written[row].append(token)
                    going[row] = token != END and len(written[row]) < steps
            tokens = torch.tensor(chosen)[:, None]
    return written
