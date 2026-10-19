import json
import math
import os
import struct

import torch
import torch.nn.functional as F

FILE = "data/model.safetensors"
VOCAB, WIDTH, HIDDEN, LAYERS = 49152, 576, 1536, 30
HEADS, KV_HEADS, THETA, EPS = 9, 3, 100000.0, 1e-5
# The app's opening line, cut before its name.
OPENING, CUT, LIKELIEST = "Once upon a time, there was a little girl named Lily.", 2, 3


def tensors(path):
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
    return found, header


def rotate(x, positions, theta):
    dim = x.shape[-1]
    frequencies = theta ** (-torch.arange(0, dim, 2, dtype=torch.float64) / dim)
    angles = positions.to(torch.float64)[..., None] * frequencies
    cos, sin = angles.cos().to(x.dtype), angles.sin().to(x.dtype)
    first, second = x[..., : dim // 2], x[..., dim // 2 :]
    return torch.cat([first * cos - second * sin, second * cos + first * sin], dim=-1)


def rms_norm(x, weight, eps=EPS):
    return weight * x / torch.sqrt(x.pow(2).mean(dim=-1, keepdim=True) + eps)


def logits(w, tokens):
    """SmolLM2's logits for tokens, in float64, from its tensors."""
    x = w["model.embed_tokens.weight"][tokens]
    length, dim = len(tokens), WIDTH // HEADS
    positions = torch.arange(length)
    for n in range(LAYERS):
        p = {
            name.removeprefix(f"model.layers.{n}."): t
            for name, t in w.items()
            if name.startswith(f"model.layers.{n}.")
        }
        h = rms_norm(x, p["input_layernorm.weight"])
        q = (
            (h @ p["self_attn.q_proj.weight"].T)
            .view(length, HEADS, dim)
            .transpose(0, 1)
        )
        k = (
            (h @ p["self_attn.k_proj.weight"].T)
            .view(length, KV_HEADS, dim)
            .transpose(0, 1)
        )
        v = (
            (h @ p["self_attn.v_proj.weight"].T)
            .view(length, KV_HEADS, dim)
            .transpose(0, 1)
        )
        q, k = rotate(q, positions, THETA), rotate(k, positions, THETA)
        group = HEADS // KV_HEADS
        k, v = k.repeat_interleave(group, dim=0), v.repeat_interleave(group, dim=0)
        mixed = F.scaled_dot_product_attention(q, k, v, is_causal=True)
        x = (
            x
            + mixed.transpose(0, 1).reshape(length, WIDTH)
            @ p["self_attn.o_proj.weight"].T
        )
        h = rms_norm(x, p["post_attention_layernorm.weight"])
        gate, up = h @ p["mlp.gate_proj.weight"].T, h @ p["mlp.up_proj.weight"].T
        x = x + (F.silu(gate) * up) @ p["mlp.down_proj.weight"].T
    return rms_norm(x, w["model.norm.weight"]) @ w["model.embed_tokens.weight"].T


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


def figures():
    weights, header = tensors(FILE)
    assert {entry["dtype"] for entry in header.values()} == {"BF16"}
    parameters = sum(math.prod(entry["shape"]) for entry in header.values())
    embedding = VOCAB * WIDTH
    block = (parameters - embedding - WIDTH) // LAYERS
    dim, group = WIDTH // HEADS, HEADS // KV_HEADS
    kv = 2 * WIDTH * KV_HEADS * dim
    kv_full = 2 * WIDTH * HEADS * dim
    mlp = 3 * WIDTH * HIDDEN
    assert HIDDEN * 3 == 2 * 4 * WIDTH and mlp == 2 * WIDTH * 4 * WIDTH
    tokenizer = json.loads(open("data/tokenizer.json", encoding="utf-8").read())
    vocabulary = tokenizer["model"]["vocab"]
    recorded = json.loads(open("references/tokens.json", encoding="utf-8").read())
    tokens = next(t["tokens"] for t in recorded["texts"] if t["text"] == OPENING)
    prompt = tokens[:-CUT]
    w = {name: t.double() for name, t in weights.items()}
    with torch.no_grad():
        chances = logits(w, torch.tensor(prompt))[-1].softmax(-1)
    likeliest = chances.topk(LIKELIEST)
    shares = []
    for token, chance in zip(likeliest.indices.tolist(), likeliest.values.tolist()):
        share = chance * 100
        assert abs(share * 10 % 1 - 0.5) > 1e-4
        shares.append(f"{decode([token], vocabulary).strip()}, {share:.1f}%")
    bfloat16, float32 = torch.finfo(torch.bfloat16), torch.finfo(torch.float32)
    assert bfloat16.tiny == float32.tiny
    return {
        "parameters": f"{parameters:,}",
        "file_bytes": f"{os.path.getsize(FILE):,}",
        "bf16_bits": str(-int(math.log2(bfloat16.eps))),
        "float32_bits": str(-int(math.log2(float32.eps))),
        "embedding": f"{embedding:,}",
        "embedding_share": f"{embedding / parameters:.0%}",
        "block": f"{block:,}",
        "layers": str(LAYERS),
        "width": str(WIDTH),
        "heads": str(HEADS),
        "kv_heads": str(KV_HEADS),
        "group": str(group),
        "dim": str(dim),
        "kv": f"{kv:,}",
        "kv_full": f"{kv_full:,}",
        "saved": f"{(kv_full - kv) * LAYERS:,}",
        "hidden": f"{HIDDEN:,}",
        "four_width": f"{4 * WIDTH:,}",
        "mlp": f"{mlp:,}",
        "layer_norm": f"{2 * WIDTH:,}",
        "prompt": decode(prompt, vocabulary),
        "likeliest": str(LIKELIEST),
        "shares": "; ".join(shares),
    }
