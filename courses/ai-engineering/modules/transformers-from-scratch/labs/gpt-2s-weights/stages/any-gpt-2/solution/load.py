"""Any GPT-2, from its safetensors file: its configuration worked out from its tensors, and a
damaged file refused."""

import json
import math
import os
import re
import struct

import torch

import gpt2

# The width of each head in every one of GPT-2's sizes.
HEAD = 64


def parts(width):
    """The shape of each tensor of a block of GPT-2 this wide, by its name in the block."""
    return {
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
    }


def configuration(header):
    """The (vocab, context, width, layers, heads) of the GPT-2 whose safetensors header this is,
    as your header gives it. Raises ValueError when its tensors aren't a GPT-2's."""
    for name in ["wte.weight", "wpe.weight"]:
        if name not in header or len(header[name]["shape"]) != 2:
            raise ValueError(f"{name} isn't an embedding")
    vocab, width = header["wte.weight"]["shape"]
    context = header["wpe.weight"]["shape"][0]
    if width % HEAD:
        raise ValueError(f"a width of {width} isn't a whole number of heads")
    blocks = [re.match(r"h\.(\d+)\.", name) for name in header]
    layers = 1 + max((int(block.group(1)) for block in blocks if block), default=-1)
    expected = {
        "wte.weight": [vocab, width],
        "wpe.weight": [context, width],
        "ln_f.weight": [width],
        "ln_f.bias": [width],
    }
    for layer in range(layers):
        for part, shape in parts(width).items():
            expected[f"h.{layer}.{part}"] = shape
    for name, shape in expected.items():
        if name not in header:
            raise ValueError(f"{name} is missing")
        if header[name]["shape"] != shape:
            raise ValueError(f"{name} is {header[name]['shape']}, not {shape}")
    for name in header:
        if name not in expected and not re.fullmatch(r"h\.\d+\.attn\.bias", name):
            raise ValueError(f"GPT-2 has no {name}")
    return vocab, context, width, layers, width // HEAD


def read(path):
    """The header of the safetensors file at path, without __metadata__, and the bytes after
    it, once the file is checked against the header. Raises ValueError when it's damaged."""
    with open(path, "rb") as file:
        length = os.fstat(file.fileno()).st_size
        if length < 8:
            raise ValueError("the file is too short to hold its header's length")
        (size,) = struct.unpack("<Q", file.read(8))
        if size > length - 8:
            raise ValueError(
                f"a header of {size:,} bytes runs past the end of the file"
            )
        try:
            header = json.loads(file.read(size).decode())
        except ValueError as error:
            raise ValueError(f"the header isn't JSON: {error}") from None
        buffer = bytearray(file.read())
    if not isinstance(header, dict):
        raise ValueError("the header isn't a JSON object")
    header.pop("__metadata__", None)
    spans = []
    for name, entry in header.items():
        if entry["dtype"] != "F32":
            raise ValueError(f"{name} is {entry['dtype']}, not F32")
        begin, end = entry["data_offsets"]
        if end - begin != 4 * math.prod(entry["shape"]):
            raise ValueError(f"{name}'s bytes don't fit its shape")
        spans.append((begin, end, name))
    at = 0
    for begin, end, name in sorted(spans):
        if begin != at:
            raise ValueError(f"{name} doesn't begin where the tensor before it ends")
        at = end
    if at != len(buffer):
        raise ValueError("the tensors don't end where the file does")
    return header, buffer


def load(path):
    """The GPT-2 in the safetensors file at path: a GPT of its configuration, with every
    parameter copied from the file, in evaluation mode. Raises ValueError when the file is
    damaged or its tensors aren't a GPT-2's."""
    header, buffer = read(path)
    model = gpt2.GPT(*configuration(header))
    weights = {}
    for name, entry in header.items():
        begin, end = entry["data_offsets"]
        numbers = torch.frombuffer(
            buffer, dtype=torch.float32, offset=begin, count=(end - begin) // 4
        )
        weights[name] = numbers.reshape(entry["shape"])
    return gpt2.load(model, weights).eval()
