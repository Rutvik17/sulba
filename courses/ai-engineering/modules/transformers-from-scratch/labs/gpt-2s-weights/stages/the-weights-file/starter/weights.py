"""GPT-2's weights, read from their safetensors file by hand."""

import json
import struct

import torch


def header(path):
    """Each tensor in the safetensors file at path, by its name: its dtype, its shape and its
    data_offsets, as the file's header gives them, without the header's __metadata__."""
    raise NotImplementedError


def tensors(path):
    """Each tensor in the file at path, by its name, as a float32 tensor of its shape. Every
    tensor in GPT-2's file is F32."""
    raise NotImplementedError
