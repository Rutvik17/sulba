import json
import struct

import torch
import torch.nn.functional as F
from torch import nn

FILE = "data/model.safetensors"
VOCAB, WIDTH, HIDDEN, LAYERS = 49152, 576, 1536, 30
HEADS, KV_HEADS, THETA, EPS = 9, 3, 100000.0, 1e-5
END = 0
# The app's opening line, and the tokens each story shows.
OPENING = "Once upon a time, there was a little girl named Lily."
WRITTEN = 20


def frequencies(dim, theta):
    """The angle each of a head's dim // 2 pairs turns through a position: theta ** (-2i / dim)
    for pair i, as a float64 tensor."""
    return theta ** (-torch.arange(0, dim, 2, dtype=torch.float64) / dim)


def rotate(x, positions, theta):
    """x (..., length, dim) with the row at each position turned by its angles, number i paired
    with number i + dim // 2. positions holds the position of each row, and its leading
    dimensions broadcast with x's. In x's dtype."""
    dim = x.shape[-1]
    angles = positions.to(torch.float64)[..., None] * frequencies(dim, theta)
    cos, sin = angles.cos().to(x.dtype), angles.sin().to(x.dtype)
    first, second = x[..., : dim // 2], x[..., dim // 2 :]
    return torch.cat([first * cos - second * sin, second * cos + first * sin], dim=-1)


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


class Cache:
    """The keys and values of every token read so far: for each block, a tensor (kv_heads,
    length, 64) of keys, already rotated, and one of values."""

    def __init__(self, layers):
        self.keys = [None] * layers
        self.values = [None] * layers

    def __len__(self):
        """The tokens it holds."""
        return 0 if self.keys[0] is None else self.keys[0].shape[-2]


def step(model, tokens, cache, problem=None):
    """The logits for tokens, which follow the tokens the cache holds: right, or with one of
    the assistant's problems with positions, the shared heads or what each token reads."""
    start, length = len(cache), len(tokens)
    if problem == "positions":
        at = torch.arange(length)
    else:
        at = torch.arange(start, start + length)
    reads = torch.ones(length, start + length, dtype=torch.bool)
    reads = reads.tril() if problem == "reads" else reads.tril(start)
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
        if problem == "shared":
            k, v = k.repeat(group, 1, 1), v.repeat(group, 1, 1)
        else:
            k, v = k.repeat_interleave(group, dim=0), v.repeat_interleave(group, dim=0)
        mixed = F.scaled_dot_product_attention(q, k, v, attn_mask=reads)
        x = x + attention.o_proj(mixed.transpose(0, 1).reshape(length, -1))
        x = x + layer.mlp(layer.post_attention_layernorm(x))
    return model.norm(x) @ model.embed_tokens.weight.T


def story(model, prompt, cache, problem=None):
    """WRITTEN tokens after prompt, each the likeliest, which must stand clear of the next
    likeliest by far more than float64's last digits differ between machines. With the
    problem "first", each token comes from the first row of logits, not the last."""
    written, tokens = [], torch.tensor(prompt)
    row = 0 if problem == "first" else -1
    with torch.no_grad():
        while len(written) < WRITTEN and END not in written:
            top = step(model, tokens, cache, problem)[row].topk(2)
            assert top.values[0] - top.values[1] > 1e-6
            written.append(int(top.indices[0]))
            tokens = torch.tensor(written[-1:])
    return written


def byte_characters():
    """GPT-2's character for each byte, which SmolLM2's tokenizer uses too."""
    kept = [*range(33, 127), *range(161, 173), *range(174, 256)]
    moved = [byte for byte in range(256) if byte not in kept]
    found = {byte: chr(byte) for byte in kept}
    found |= {byte: chr(256 + n) for n, byte in enumerate(moved)}
    return found


def decode(tokens, vocabulary):
    strings = {number: string for string, number in vocabulary.items()}
    to_byte = {character: byte for byte, character in byte_characters().items()}
    text = "".join(strings[token] for token in tokens)
    return " ".join(bytes(map(to_byte.get, text)).decode(errors="replace").split())


def figures():
    tokenizer = json.loads(open("data/tokenizer.json", encoding="utf-8").read())
    vocabulary = tokenizer["model"]["vocab"]
    recorded = json.loads(open("references/tokens.json", encoding="utf-8").read())
    opening = next(t["tokens"] for t in recorded["texts"] if t["text"] == OPENING)
    torch.set_default_dtype(torch.float64)
    model = smollm()
    torch.set_default_dtype(torch.float32)

    def told(written):
        return decode(written, vocabulary)

    group = HEADS // KV_HEADS
    return {
        "opening": OPENING,
        "right": told(story(model, opening, Cache(LAYERS))),
        "positions": told(story(model, opening, Cache(LAYERS), "positions")),
        "shared": told(story(model, opening, Cache(LAYERS), "shared")),
        "reads": told(story(model, opening, Cache(LAYERS), "reads")),
        "first": told(story(model, opening, Cache(LAYERS), "first")),
        "first_word": told(opening[:1]),
        "group": str(group),
        "heads": str(HEADS),
        "right_heads": str(
            sum(head % KV_HEADS == head // group for head in range(HEADS))
        ),
    }
