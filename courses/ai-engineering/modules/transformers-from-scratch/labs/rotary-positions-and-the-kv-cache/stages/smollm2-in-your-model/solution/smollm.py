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
    return weight * x / torch.sqrt(x.pow(2).mean(dim=-1, keepdim=True) + eps)


class RMSNorm(nn.Module):
    """rms_norm with a learnt weight, which starts at ones."""

    def __init__(self, width, eps=EPS):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(width))
        self.eps = eps

    def forward(self, x):
        return rms_norm(x, self.weight, self.eps)


class MLP(nn.Module):
    """SwiGLU: down_proj(silu(gate_proj(x)) * up_proj(x)), with no biases."""

    def __init__(self, width, hidden):
        super().__init__()
        self.gate_proj = nn.Linear(width, hidden, bias=False)
        self.up_proj = nn.Linear(width, hidden, bias=False)
        self.down_proj = nn.Linear(hidden, width, bias=False)

    def forward(self, x):
        return self.down_proj(F.silu(self.gate_proj(x)) * self.up_proj(x))


class Attention(nn.Module):
    """Causal attention with heads query heads, each width // heads wide, and kv_heads key
    and value heads, each shared by heads // kv_heads neighbouring query heads. Queries and
    keys are rotated by their positions. No biases. Keeps heads and kv_heads as attributes."""

    def __init__(self, width, heads, kv_heads):
        super().__init__()
        self.heads, self.kv_heads, self.dim = heads, kv_heads, width // heads
        self.q_proj = nn.Linear(width, heads * self.dim, bias=False)
        self.k_proj = nn.Linear(width, kv_heads * self.dim, bias=False)
        self.v_proj = nn.Linear(width, kv_heads * self.dim, bias=False)
        self.o_proj = nn.Linear(heads * self.dim, width, bias=False)

    def forward(self, x):
        batch, length, _ = x.shape
        q = self.q_proj(x).view(batch, length, self.heads, self.dim).transpose(1, 2)
        k = self.k_proj(x).view(batch, length, self.kv_heads, self.dim).transpose(1, 2)
        v = self.v_proj(x).view(batch, length, self.kv_heads, self.dim).transpose(1, 2)
        positions = torch.arange(length)
        q, k = rotate(q, positions, THETA), rotate(k, positions, THETA)
        group = self.heads // self.kv_heads
        k, v = k.repeat_interleave(group, dim=1), v.repeat_interleave(group, dim=1)
        mixed = F.scaled_dot_product_attention(q, k, v, is_causal=True)
        return self.o_proj(mixed.transpose(1, 2).reshape(batch, length, -1))


class Block(nn.Module):
    """input_layernorm, self_attn, post_attention_layernorm and mlp, each part added to the
    stream after normalizing its input."""

    def __init__(self, width, hidden, heads, kv_heads):
        super().__init__()
        self.input_layernorm = RMSNorm(width)
        self.self_attn = Attention(width, heads, kv_heads)
        self.post_attention_layernorm = RMSNorm(width)
        self.mlp = MLP(width, hidden)

    def forward(self, x):
        x = x + self.self_attn(self.input_layernorm(x))
        return x + self.mlp(self.post_attention_layernorm(x))


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
        self.embed_tokens = nn.Embedding(vocab, width)
        self.layers = nn.ModuleList(
            Block(width, hidden, heads, kv_heads) for _ in range(layers)
        )
        self.norm = RMSNorm(width)

    def forward(self, tokens):
        """The logits (batch, length, vocab) for tokens (batch, length)."""
        x = self.embed_tokens(tokens)
        for layer in self.layers:
            x = layer(x)
        return self.norm(x) @ self.embed_tokens.weight.T


def smollm(path=FILE):
    """SmolLM2-135M, with the weights in the file at path, in evaluation mode."""
    model = SmolLM()
    weights = {name.removeprefix("model."): t for name, t in tensors(path).items()}
    model.load_state_dict(weights)
    return model.eval()
