import json
import re
import struct

import regex
import torch

FILE = "data/model.safetensors"
# The reading app's opening line, the tokens GPT-2 writes after it, and a shorter prompt.
OPENING = "Once upon a time, there was a little girl named Lily."
WRITTEN, PROMPT, LIKELIEST = 20, "Once upon a", 3


def read_header(file):
    """The header of the open file, which starts with its length in 8 bytes, little-endian."""
    (size,) = struct.unpack("<Q", file.read(8))
    found = json.loads(file.read(size))
    found.pop("__metadata__", None)
    return found


def header(path):
    """Each tensor in the safetensors file at path, by its name: its dtype, its shape and its
    data_offsets, as the file's header gives them, without the header's __metadata__."""
    with open(path, "rb") as file:
        return read_header(file)


def tensors(path):
    """Each tensor in the file at path, by its name, as a float32 tensor of its shape. Every
    tensor in GPT-2's file is F32."""
    with open(path, "rb") as file:
        found = read_header(file)
        buffer = bytearray(file.read())
    read = {}
    for name, entry in found.items():
        begin, end = entry["data_offsets"]
        numbers = torch.frombuffer(
            buffer, dtype=torch.float32, offset=begin, count=(end - begin) // 4
        )
        read[name] = numbers.reshape(entry["shape"])
    return read


# GPT-2's pattern, which splits text into the pieces that merges stay inside: a word with the
# space before it, a number, a run of other marks, or spaces.
PATTERN = regex.compile(
    r"""'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""
)
# The separator between documents, a token of its own.
END = "<|endoftext|>"


def byte_characters():
    """Each byte's character in GPT-2's vocabulary, by the byte: the bytes that print as
    themselves in Latin-1 keep their character, and the others take characters from U+0100 on,
    in the order of the bytes."""
    printed = [*range(ord("!"), ord("~") + 1), *range(ord("¡"), ord("¬") + 1)]
    printed += range(ord("®"), ord("ÿ") + 1)
    characters, moved = {}, 0
    for byte in range(256):
        if byte in printed:
            characters[byte] = chr(byte)
        else:
            characters[byte] = chr(256 + moved)
            moved += 1
    return characters


def load_tokenizer(folder):
    """GPT-2's vocabulary, each token's number by its string, from vocab.json in folder, and
    its merges, each a pair of strings, in the order merges.txt lists them."""
    with open(f"{folder}/vocab.json", encoding="utf-8") as file:
        vocabulary = json.load(file)
    with open(f"{folder}/merges.txt", encoding="utf-8") as file:
        lines = file.read().split("\n")[1:]
    return vocabulary, [tuple(line.split(" ")) for line in lines if line]


def merged(piece, ranks):
    """The piece's strings once every merge it allows is made, lowest rank first."""
    parts = list(piece)
    while len(parts) > 1:
        pairs = list(zip(parts, parts[1:]))
        best = min(pairs, key=lambda pair: ranks.get(pair, len(ranks)))
        if best not in ranks:
            break
        joined, at = [], 0
        while at < len(parts):
            if tuple(parts[at : at + 2]) == best:
                joined.append(parts[at] + parts[at + 1])
                at += 2
            else:
                joined.append(parts[at])
                at += 1
        parts = joined
    return parts


def encode(text, vocabulary, merges):
    """The text's tokens: each END in it as END's token, and each piece of the text between,
    as PATTERN splits it, merged pair by pair, the pair merged first being the one listed
    first."""
    characters = byte_characters()
    ranks = {pair: rank for rank, pair in enumerate(merges)}
    tokens = []
    for at, part in enumerate(text.split(END)):
        if at:
            tokens.append(vocabulary[END])
        for piece in PATTERN.findall(part):
            mapped = "".join(characters[byte] for byte in piece.encode())
            tokens.extend(vocabulary[string] for string in merged(mapped, ranks))
    return tokens


def decode(tokens, vocabulary):
    """The text the tokens stand for."""
    strings = {number: string for string, number in vocabulary.items()}
    to_byte = {character: byte for byte, character in byte_characters().items()}
    text = "".join(strings[token] for token in tokens)
    return bytes(to_byte[character] for character in text).decode(errors="replace")


def layer_norm(x, weight, bias, eps=1e-5):
    """x normalized along its last dimension: less its mean, over the square root of its
    variance plus eps, then times weight and plus bias."""
    mean = x.mean(dim=-1, keepdim=True)
    variance = (x - mean).pow(2).mean(dim=-1, keepdim=True)
    return (x - mean) / torch.sqrt(variance + eps) * weight + bias


class LayerNorm(torch.nn.Module):
    """Layer normalization with a weight, starting at 1, and a bias, starting at 0."""

    def __init__(self, width, eps=1e-5):
        super().__init__()
        self.weight = torch.nn.Parameter(torch.ones(width))
        self.bias = torch.nn.Parameter(torch.zeros(width))
        self.eps = eps

    def forward(self, x):
        return layer_norm(x, self.weight, self.bias, self.eps)


class CausalSelfAttention(torch.nn.Module):
    """Causal self-attention in heads, as you built it in the Attention lab: its query, key
    and value layers in one, qkv, as GPT-2 holds them, and an output layer, out."""

    def __init__(self, width, heads):
        super().__init__()
        self.heads = heads
        self.qkv = torch.nn.Linear(width, 3 * width)
        self.out = torch.nn.Linear(width, width)

    def forward(self, x):
        batch, length, width = x.shape
        q, k, v = (
            part.view(batch, length, self.heads, width // self.heads).transpose(1, 2)
            for part in self.qkv(x).split(width, dim=-1)
        )
        mixed = torch.nn.functional.scaled_dot_product_attention(
            q, k, v, is_causal=True
        )
        return self.out(mixed.transpose(1, 2).reshape(batch, length, width))


def gelu(x):
    """GELU in the tanh form GPT-2 uses."""
    return 0.5 * x * (1 + torch.tanh((2 / torch.pi) ** 0.5 * (x + 0.044715 * x**3)))


class MLP(torch.nn.Module):
    """A linear layer to four times the width, fc, GELU, and a linear layer back, proj."""

    def __init__(self, width):
        super().__init__()
        self.fc = torch.nn.Linear(width, 4 * width)
        self.proj = torch.nn.Linear(4 * width, width)

    def forward(self, x):
        return self.proj(gelu(self.fc(x)))


class Block(torch.nn.Module):
    """ln_1 and attn, then ln_2 and mlp, each adding its output to the residual stream."""

    def __init__(self, width, heads):
        super().__init__()
        self.ln_1 = LayerNorm(width)
        self.attn = CausalSelfAttention(width, heads)
        self.ln_2 = LayerNorm(width)
        self.mlp = MLP(width)

    def forward(self, x):
        x = x + self.attn(self.ln_1(x))
        return x + self.mlp(self.ln_2(x))


class GPT(torch.nn.Module):
    """GPT-2's model: token and position embeddings, the blocks, a final layer
    normalization, and an output layer that is the token embeddings' own weight."""

    def __init__(self, vocab, context, width, layers, heads):
        super().__init__()
        self.context = context
        self.wte = torch.nn.Embedding(vocab, width)
        self.wpe = torch.nn.Embedding(context, width)
        self.blocks = torch.nn.ModuleList(Block(width, heads) for _ in range(layers))
        self.ln_f = LayerNorm(width)
        for name, param in self.named_parameters():
            if name.endswith(("attn.out.weight", "mlp.proj.weight")):
                torch.nn.init.normal_(param, std=0.02 / (2 * layers) ** 0.5)
            elif param.dim() == 2:
                torch.nn.init.normal_(param, std=0.02)
            elif name.endswith("bias"):
                torch.nn.init.zeros_(param)

    def forward(self, tokens):
        """The logits (batch, length, vocab) for tokens (batch, length). Raises ValueError for
        a story longer than the context."""
        length = tokens.shape[-1]
        if length > self.context:
            raise ValueError(f"{length} tokens don't fit a context of {self.context}")
        x = self.wte(tokens) + self.wpe(torch.arange(length, device=tokens.device))
        for block in self.blocks:
            x = block(x)
        return self.ln_f(x) @ self.wte.weight.T


# Each linear layer's name in GPT-2's file, and its name in your GPT.
LINEARS = {
    "attn.c_attn": "attn.qkv",
    "attn.c_proj": "attn.out",
    "mlp.c_fc": "mlp.fc",
    "mlp.c_proj": "mlp.proj",
}


def renamed(name):
    """A tensor's name in GPT-2's file as its parameter's name in your GPT, and whether the
    tensor is a linear layer's weight, which GPT-2 keeps as (inputs, outputs)."""
    block = re.fullmatch(r"h\.(\d+)\.(.+)\.(weight|bias)", name)
    if not block:
        return name, False
    number, part, kind = block.groups()
    target = f"blocks.{number}.{LINEARS.get(part, part)}.{kind}"
    return target, part in LINEARS and kind == "weight"


def load(model, weights):
    """The model, with GPT-2's weights, a tensor for each name in its file, copied into its
    parameters. Raises ValueError when a tensor has no parameter to go to, or a parameter has no
    tensor."""
    parameters = dict(model.named_parameters())
    unset = set(parameters)
    with torch.no_grad():
        for name, tensor in weights.items():
            if re.fullmatch(r"h\.\d+\.attn\.bias", name):
                continue
            target, transposed = renamed(name)
            if target not in unset:
                raise ValueError(f"{name} has no parameter to go to")
            parameters[target].copy_(tensor.T if transposed else tensor)
            unset.remove(target)
    if unset:
        raise ValueError(f"{min(unset)} and {len(unset) - 1} more have no tensor")
    return model


def figures():
    vocabulary, merges = load_tokenizer("data")
    weights = tensors(FILE)
    torch.manual_seed(0)
    torch.set_default_dtype(torch.float64)
    model = load(GPT(50257, 1024, 768, 12, 12), weights).eval()
    torch.set_default_dtype(torch.float32)
    tokens = encode(OPENING, vocabulary, merges)
    written = []
    with torch.no_grad():
        for _ in range(WRITTEN):
            logits = model(torch.tensor([tokens + written]))[0, -1]
            top = logits.topk(2)
            # Clear of a tie by far more than float64's last digits, which differ a little
            # from one machine to another.
            assert top.values[0] - top.values[1] > 1e-6
            written.append(int(top.indices[0]))
        prompt = encode(PROMPT, vocabulary, merges)
        chances = model(torch.tensor([prompt]))[0, -1].softmax(-1)
    likeliest = chances.topk(LIKELIEST)
    shares = []
    for token, chance in zip(likeliest.indices.tolist(), likeliest.values.tolist()):
        share = chance * 100
        assert abs(share * 10 % 1 - 0.5) > 1e-4
        shares.append(f"{decode([token], vocabulary).strip()}, {share:.1f}%")
    masks = [name for name in weights if re.fullmatch(r"h\.\d+\.attn\.bias", name)]
    width = model.wte.weight.shape[1]
    return {
        "opening": OPENING,
        "written": str(WRITTEN),
        "continuation": " ".join(decode(written, vocabulary).split()),
        "prompt": PROMPT,
        "likeliest": str(LIKELIEST),
        "shares": "; ".join(shares),
        "tensors": str(len(weights)),
        "copied": str(len(weights) - len(masks)),
        "transposed": str(sum(renamed(name)[1] for name in weights)),
        "vocab": f"{len(vocabulary):,}",
        "context": f"{model.context:,}",
        "width": str(width),
        "blocks": str(len(model.blocks)),
        "heads": str(model.blocks[0].attn.heads),
    }
