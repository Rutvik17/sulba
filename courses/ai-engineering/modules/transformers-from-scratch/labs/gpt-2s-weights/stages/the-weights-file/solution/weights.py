"""GPT-2's weights, read from their safetensors file by hand."""

import json
import struct

import torch


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
