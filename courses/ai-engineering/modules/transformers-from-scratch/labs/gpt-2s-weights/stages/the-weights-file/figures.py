import json
import math
import os
import re
import struct

FILE = "data/model.safetensors"


def figures():
    with open(FILE, "rb") as file:
        (size,) = struct.unpack("<Q", file.read(8))
        found = json.loads(file.read(size))
    found.pop("__metadata__")
    assert {entry["dtype"] for entry in found.values()} == {"F32"}
    masks = [name for name in found if re.fullmatch(r"h\.\d+\.attn\.bias", name)]
    counts = {name: math.prod(entry["shape"]) for name, entry in found.items()}
    mask_bytes = 4 * sum(counts[name] for name in masks)
    file_bytes = os.path.getsize(FILE)
    layers = {int(name.split(".")[1]) for name in found if name.startswith("h.")}
    return {
        "file_bytes": f"{file_bytes:,}",
        "header_bytes": f"{size:,}",
        "tensors": str(len(found)),
        "layers": str(len(layers)),
        "masks": str(len(masks)),
        "mask_shape": " × ".join(map(str, found[masks[0]]["shape"])),
        "mask_bytes": f"{mask_bytes:,}",
        "mask_share": f"{mask_bytes / file_bytes:.0%}",
        "parameter_tensors": str(len(found) - len(masks)),
        "parameters": f"{sum(counts[name] for name in found if name not in masks):,}",
    }
