import json
import math
import random
import re
import struct

import pytest
import torch
import torch.nn.functional as F

from load import configuration, load

# GPT-2's vocabulary and context, and its four sizes as (width, layers, heads), from the
# hparams.json OpenAI published with each.
VOCAB, CONTEXT = 50257, 1024
SIZES = [(768, 12, 12), (1024, 24, 16), (1280, 36, 20), (1600, 48, 25)]
HEAD = 64


def shapes(vocab, context, width, layers, masks=True):
    """The shape of each tensor of a GPT-2 of this configuration, by its name."""
    found = {"wte.weight": [vocab, width], "wpe.weight": [context, width]}
    for block in range(layers):
        for part, shape in {
            "ln_1.weight": [width],
            "ln_1.bias": [width],
            "attn.c_attn.weight": [width, 3 * width],
            "attn.c_attn.bias": [3 * width],
            "attn.c_proj.weight": [width, width],
            "attn.c_proj.bias": [width],
            "ln_2.weight": [width],
            "ln_2.bias": [width],
            "mlp.c_fc.weight": [width, 4 * width],
            "mlp.c_fc.bias": [4 * width],
            "mlp.c_proj.weight": [4 * width, width],
            "mlp.c_proj.bias": [width],
        }.items():
            found[f"h.{block}.{part}"] = shape
        if masks:
            found[f"h.{block}.attn.bias"] = [1, 1, context, context]
    return found | {"ln_f.weight": [width], "ln_f.bias": [width]}


def entries(shapes, order, size=4, dtype="F32"):
    """A header's entries for tensors of these shapes, their bytes one after another in this
    order, each number size bytes."""
    found, at = {}, 0
    for name in order:
        end = at + size * math.prod(shapes[name])
        found[name] = {"dtype": dtype, "shape": shapes[name], "data_offsets": [at, end]}
        at = end
    return found


def drawn(shapes, seed):
    """A tensor of each shape, its numbers drawn at random, and each mask causal."""
    generator = torch.Generator().manual_seed(seed)
    found = {}
    for name, shape in shapes.items():
        if re.fullmatch(r"h\.\d+\.attn\.bias", name):
            found[name] = torch.ones(shape).tril()
        elif "ln_" in name and name.endswith("weight"):
            found[name] = 1 + 0.1 * torch.randn(shape, generator=generator)
        else:
            found[name] = 0.2 * torch.randn(shape, generator=generator)
    return found


def stored(tensors, order, dtype="<f4"):
    """The tensors' bytes, little-endian, one after another in this order."""
    return b"".join(tensors[name].numpy().astype(dtype).tobytes() for name in order)


def packed(header, data, metadata=None, padding=0):
    """A safetensors file: the header's length, the header with __metadata__ and that many
    spaces after it, then the data."""
    if metadata is not None:
        header = {"__metadata__": metadata} | header
    text = json.dumps(header).encode() + b" " * padding
    return struct.pack("<Q", len(text)) + text + data


def written(folder, name, data):
    path = folder / name
    path.write_bytes(data)
    return path


def logits(tensors, heads, tokens):
    """GPT-2's logits for tokens, in float64, worked out from its tensors."""
    w = {name: tensor.double() for name, tensor in tensors.items()}
    length, width = len(tokens), w["wte.weight"].shape[1]
    x = w["wte.weight"][tokens] + w["wpe.weight"][:length]
    block = 0
    while f"h.{block}.ln_1.weight" in w:
        p = {
            name.removeprefix(f"h.{block}."): tensor
            for name, tensor in w.items()
            if name.startswith(f"h.{block}.")
        }
        h = F.layer_norm(x, (width,), p["ln_1.weight"], p["ln_1.bias"], 1e-5)
        q, k, v = (
            part.view(length, heads, -1).transpose(0, 1)
            for part in (h @ p["attn.c_attn.weight"] + p["attn.c_attn.bias"]).split(
                width, dim=-1
            )
        )
        mixed = F.scaled_dot_product_attention(q, k, v, is_causal=True)
        mixed = mixed.transpose(0, 1).reshape(length, width)
        x = x + mixed @ p["attn.c_proj.weight"] + p["attn.c_proj.bias"]
        h = F.layer_norm(x, (width,), p["ln_2.weight"], p["ln_2.bias"], 1e-5)
        h = F.gelu(h @ p["mlp.c_fc.weight"] + p["mlp.c_fc.bias"], approximate="tanh")
        x = x + h @ p["mlp.c_proj.weight"] + p["mlp.c_proj.bias"]
        block += 1
    x = F.layer_norm(x, (width,), w["ln_f.weight"], w["ln_f.bias"], 1e-5)
    return x @ w["wte.weight"].T


def refusals(folder, files, record_property):
    """Asserts that load raises ValueError for each file, noting the ones it doesn't."""
    missed = []
    for number, (kind, data) in enumerate(files.items()):
        path = written(folder, f"{number}.safetensors", data)
        try:
            load(path)
        except ValueError:
            continue
        except Exception as error:
            missed.append(f"{kind} ({type(error).__name__})")
        else:
            missed.append(f"{kind} (loaded)")
    note = f"{len(files) - len(missed)} of {len(files)} refused."
    if missed:
        note += f" Not refused: {', '.join(missed)}."
    record_property("note", note)
    assert not missed


def file(tensors):
    """A safetensors file of these tensors, stored in their names' order."""
    order = sorted(tensors)
    sizes = {name: list(tensor.shape) for name, tensor in tensors.items()}
    return packed(entries(sizes, order), stored(tensors, order))


def others():
    """Files of GPT-2s of other sizes, each with its tensors: their bytes in another order
    than their header lists them, and the masks or __metadata__ there or not."""
    for seed, (vocab, context, width, layers, masks) in enumerate(
        [(300, 40, 128, 2, True), (77, 16, 64, 1, False), (512, 64, 192, 3, True)]
    ):
        found = shapes(vocab, context, width, layers, masks)
        tensors = drawn(found, seed)
        order = sorted(found)
        random.Random(seed).shuffle(order)
        header = entries(found, order)
        listed = sorted(header, reverse=seed == 1)
        data = packed(
            {name: header[name] for name in listed},
            stored(tensors, order),
            metadata={"format": "pt"} if seed != 1 else None,
            padding=5 * seed,
        )
        yield data, tensors


def damaged():
    """Damaged files of a small GPT-2, by what is wrong with each."""
    found = shapes(100, 16, 64, 2)
    tensors = drawn(found, 7)
    order = sorted(found)
    header = entries(found, order)
    data = stored(tensors, order)
    whole = packed(header, data)
    unfitting = header | {"ln_f.bias": header["ln_f.bias"] | {"shape": [65]}}
    shared = [name for name in order if name != "h.1.ln_2.bias"]
    sharing = entries(found, shared)
    sharing["h.1.ln_2.bias"] = sharing["h.1.ln_2.weight"]
    first = header[order[0]]["data_offsets"][1]
    gapped = {
        name: entry | {"data_offsets": [at + 64 for at in entry["data_offsets"]]}
        if entry["data_offsets"][0] >= first
        else entry
        for name, entry in header.items()
    }
    return {
        "a file cut short": whole[: len(whole) * 2 // 3],
        "a web page saved in its place": (
            b"<!DOCTYPE html>\n<html><head><title>Not found</title></head></html>\n"
        ),
        "a header written over": whole[:40] + bytes(16) + whole[56:],
        "a tensor whose bytes don't fit its shape": packed(unfitting, data),
        "two tensors on the same bytes": packed(sharing, stored(tensors, shared)),
        "a gap between two tensors": packed(
            gapped, data[:first] + bytes(64) + data[first:]
        ),
        "bytes after the last tensor": whole + bytes(64),
        "tensors that aren't F32": packed(
            entries(found, order, size=2, dtype="F16"), stored(tensors, order, "<f2")
        ),
    }


def foreign():
    """Whole files whose tensors aren't a GPT-2's, by what is wrong with each."""
    tensors = drawn(shapes(100, 16, 64, 2), 8)
    missing = {name: t for name, t in tensors.items() if name != "h.1.mlp.c_fc.bias"}
    return {
        "a tensor missing": file(missing),
        "a tensor of the wrong shape": file(
            tensors | {"h.0.attn.c_attn.weight": torch.zeros(64, 128)}
        ),
        "a tensor GPT-2 doesn't have": file(
            tensors | {"lm_head.weight": torch.zeros(100, 64)}
        ),
        "a width that isn't a whole number of heads": file(
            drawn(shapes(100, 16, 96, 2), 9)
        ),
    }


@pytest.mark.id("tst_wnoi1x")
def test_four_sizes():
    """GPT-2's four sizes"""
    for number, (width, layers, heads) in enumerate(SIZES):
        found = shapes(VOCAB, CONTEXT, width, layers, masks=number % 2 == 0)
        order = sorted(found)
        random.Random(number).shuffle(order)
        header = entries(found, order)
        assert configuration(header) == (VOCAB, CONTEXT, width, layers, heads)


@pytest.mark.id("tst_hw4owk")
def test_other_gpt2s(tmp_path):
    """Other GPT-2s"""
    for number, (data, tensors) in enumerate(others()):
        model = load(written(tmp_path, f"{number}.safetensors", data))
        assert not model.training
        vocab, width = tensors["wte.weight"].shape
        context = tensors["wpe.weight"].shape[0]
        generator = torch.Generator().manual_seed(number)
        tokens = torch.randint(vocab, (context,), generator=generator)
        expected = logits(tensors, width // HEAD, tokens)
        with torch.no_grad():
            given = model.double()(tokens[None])[0]
        assert torch.allclose(given, expected, rtol=1e-9, atol=1e-9)


@pytest.mark.id("tst_lvrxly")
def test_damaged(tmp_path, record_property):
    """Damaged files"""
    refusals(tmp_path, damaged(), record_property)


@pytest.mark.id("tst_zxv4m0")
def test_not_gpt2(tmp_path, record_property):
    """Files that aren't GPT-2's"""
    refusals(tmp_path, foreign(), record_property)
