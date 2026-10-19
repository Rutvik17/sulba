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
    raise NotImplementedError


def generate(model, prompt, steps):
    """The tokens model writes after prompt, a list of tokens, each the likeliest, until it
    writes END, which it keeps, or has written steps tokens."""
    raise NotImplementedError
