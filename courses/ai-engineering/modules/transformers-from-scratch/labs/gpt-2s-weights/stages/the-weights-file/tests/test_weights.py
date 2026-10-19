import json
import os
import struct
from pathlib import Path

import pytest
import torch

from weights import header, tensors

FILE = "data/model.safetensors"
RECORDED = json.loads(Path("references/tensors.json").read_text())["tensors"]


@pytest.fixture(scope="module")
def read():
    return tensors(FILE)


def write(path, named, metadata):
    """A safetensors file holding the float32 tensors named, its header listing them in name
    order and padded with spaces, and their numbers stored in the reverse order."""
    stored, at = {}, 0
    for name, tensor in reversed(named.items()):
        size = 4 * tensor.numel()
        stored[name] = (tensor, [at, at + size])
        at += size
    entries = {"__metadata__": metadata}
    for name, tensor in named.items():
        entries[name] = {
            "dtype": "F32",
            "shape": list(tensor.shape),
            "data_offsets": stored[name][1],
        }
    text = json.dumps(entries).encode() + b"   "
    with open(path, "wb") as file:
        file.write(struct.pack("<Q", len(text)) + text)
        for tensor, _ in stored.values():
            file.write(tensor.numpy().tobytes())


@pytest.mark.id("tst_xvm495")
def test_header():
    """Every tensor's dtype and shape, as the safetensors library reads them"""
    found = header(FILE)
    assert sorted(found) == sorted(RECORDED)
    for name, entry in found.items():
        assert entry["dtype"] == RECORDED[name]["dtype"]
        assert entry["shape"] == RECORDED[name]["shape"]


@pytest.mark.id("tst_bxb1up")
def test_offsets():
    """Offsets that cover the bytes after the header, 4 bytes a number"""
    found = header(FILE)
    with open(FILE, "rb") as file:
        (size,) = struct.unpack("<Q", file.read(8))
    spans = sorted(entry["data_offsets"] for entry in found.values())
    at = 0
    for begin, end in spans:
        assert begin == at
        at = end
    assert at == os.path.getsize(FILE) - 8 - size
    for entry in found.values():
        begin, end = entry["data_offsets"]
        assert end - begin == 4 * torch.Size(entry["shape"]).numel()


@pytest.mark.id("tst_w9m9rw")
def test_numbers(read):
    """Every number, as the safetensors library reads it"""
    assert sorted(read) == sorted(RECORDED)
    for name, tensor in read.items():
        recorded = RECORDED[name]
        assert tensor.dtype == torch.float32
        assert list(tensor.shape) == recorded["shape"]
        flat = tensor.double().flatten()
        assert flat[recorded["places"]].tolist() == recorded["values"]
        assert flat.sum().item() == pytest.approx(recorded["sum"], rel=1e-12, abs=1e-12)
        assert flat.square().sum().item() == pytest.approx(
            recorded["squares"], rel=1e-12
        )


@pytest.mark.id("tst_dfnly9")
def test_other_files(tmp_path):
    """A file with metadata, a padded header and its numbers in another order"""
    generator = torch.Generator().manual_seed(0)
    named = {
        "bias": torch.randn(5, generator=generator),
        "scale": torch.randn((), generator=generator),
        "weight": torch.randn(3, 4, generator=generator),
    }
    path = tmp_path / "small.safetensors"
    write(path, named, {"format": "pt"})
    assert sorted(header(path)) == sorted(named)
    assert header(path)["weight"]["shape"] == [3, 4]
    read = tensors(path)
    assert sorted(read) == sorted(named)
    for name, tensor in named.items():
        assert torch.equal(read[name], tensor)
