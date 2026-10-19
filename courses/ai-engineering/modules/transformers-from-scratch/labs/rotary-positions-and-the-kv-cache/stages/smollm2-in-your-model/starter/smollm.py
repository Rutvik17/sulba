"""SmolLM2-135M in your own model: RMSNorm, a SwiGLU MLP and grouped-query attention, with
the weights from its file."""

import json
import struct

import torch
import torch.nn.functional as F
from torch import nn

from rope import rotate

# SmolLM2-135M's configuration, from its config.json.
VOCAB, WIDTH, HIDDEN, LAYERS = 49152, 576, 1536, 30
HEADS, KV_HEADS, THETA, EPS = 9, 3, 100000.0, 1e-5
FILE = "data/model.safetensors"


def tensors(path):
    """Each tensor in the safetensors file at path, by its name, as float32. SmolLM2's file
    keeps them as BF16: the first two bytes of each float32."""
    with open(path, "rb") as file:
        (size,) = struct.unpack("<Q", file.read(8))
        header = json.loads(file.read(size))
        buffer = bytearray(file.read())
    header.pop("__metadata__", None)
    found = {}
    for name, entry in header.items():
        begin, end = entry["data_offsets"]
        numbers = torch.frombuffer(
            buffer, dtype=torch.bfloat16, offset=begin, count=(end - begin) // 2
        )
        found[name] = numbers.reshape(entry["shape"]).float()
    return found


def rms_norm(x, weight, eps=EPS):
    """x over the root mean square of its last dimension, with eps added to the mean square,
    times weight."""
    raise NotImplementedError


class RMSNorm(nn.Module):
    """rms_norm with a learnt weight, which starts at ones."""

    def __init__(self, width, eps=EPS):
        super().__init__()
        raise NotImplementedError

    def forward(self, x):
        raise NotImplementedError


class MLP(nn.Module):
    """SwiGLU: down_proj(silu(gate_proj(x)) * up_proj(x)), with no biases."""

    def __init__(self, width, hidden):
        super().__init__()
        raise NotImplementedError

    def forward(self, x):
        raise NotImplementedError


class Attention(nn.Module):
    """Causal attention with heads query heads, each width // heads wide, and kv_heads key
    and value heads, each shared by heads // kv_heads neighbouring query heads. Queries and
    keys are rotated by their positions. No biases. Keeps heads and kv_heads as attributes."""

    def __init__(self, width, heads, kv_heads):
        super().__init__()
        raise NotImplementedError

    def forward(self, x):
        raise NotImplementedError


class Block(nn.Module):
    """input_layernorm, self_attn, post_attention_layernorm and mlp, each part added to the
    stream after normalizing its input."""

    def __init__(self, width, hidden, heads, kv_heads):
        super().__init__()
        raise NotImplementedError

    def forward(self, x):
        raise NotImplementedError


class SmolLM(nn.Module):
    """embed_tokens, layers and norm, its output layer the token embeddings' own weight."""

    def __init__(
        self,
        vocab=VOCAB,
        width=WIDTH,
        hidden=HIDDEN,
        layers=LAYERS,
        heads=HEADS,
        kv_heads=KV_HEADS,
    ):
        super().__init__()
        raise NotImplementedError

    def forward(self, tokens):
        """The logits (batch, length, vocab) for tokens (batch, length)."""
        raise NotImplementedError


def smollm(path=FILE):
    """SmolLM2-135M, with the weights in the file at path, in evaluation mode."""
    raise NotImplementedError
