import json
import struct

import torch
import torch.nn.functional as F
from torch import nn
from torch.utils.flop_counter import FlopCounterMode

FILE = "data/model.safetensors"
VOCAB, WIDTH, HIDDEN, LAYERS = 49152, 576, 1536, 30
HEADS, KV_HEADS, THETA, EPS = 9, 3, 100000.0, 1e-5
END = 0
# The story length the costs are worked out at, and the app's opening line.
STORY = 256
OPENING = "Once upon a time, there was a little girl named Lily."


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
    return bytes(map(to_byte.get, text)).decode(errors="replace")


def multiply_adds(run):
    """The multiply-adds of every matrix multiply run makes, as PyTorch counts them."""
    with FlopCounterMode(display=False) as counter:
        run()
    return counter.get_total_flops() // 2


def costs():
    """The multiply-adds of writing token STORY + 1, with the cache and without it."""
    with torch.device("meta"):
        model = SmolLM()
        cache = Cache(LAYERS)
        with torch.no_grad():
            step(model, torch.zeros(STORY, dtype=torch.long), cache)
            cached = multiply_adds(
                lambda: step(model, torch.zeros(1, dtype=torch.long), cache)
            )
            whole = multiply_adds(
                lambda: model(torch.zeros(1, STORY + 1, dtype=torch.long))
            )
    return cached, whole


def figures():
    cached, whole = costs()
    dim = WIDTH // HEADS
    token_bytes = 2 * LAYERS * KV_HEADS * dim * 4
    full_bytes = 2 * LAYERS * HEADS * dim * 4
    context = 8192
    vocabulary = json.loads(open("data/tokenizer.json", encoding="utf-8").read())[
        "model"
    ]["vocab"]
    recorded = json.loads(open("references/tokens.json", encoding="utf-8").read())
    prompt = next(t["tokens"] for t in recorded["texts"] if t["text"] == OPENING)
    torch.set_default_dtype(torch.float64)
    model = smollm()
    torch.set_default_dtype(torch.float32)
    written = generate(model, prompt, 30)
    return {
        "story": str(STORY),
        "cached": f"{cached:,}",
        "uncached": f"{whole:,}",
        "ratio": f"{whole / cached:.0f}",
        "token_bytes": f"{token_bytes:,}",
        "full_bytes": f"{full_bytes * context:,}",
        "context_bytes": f"{token_bytes * context:,}",
        "context": f"{context:,}",
        "heads": str(HEADS),
        "kv_heads": str(KV_HEADS),
        "dim": str(dim),
        "layers": str(LAYERS),
        "opening": OPENING,
        "written": str(len(written)),
        "continuation": decode(written, vocabulary),
    }
