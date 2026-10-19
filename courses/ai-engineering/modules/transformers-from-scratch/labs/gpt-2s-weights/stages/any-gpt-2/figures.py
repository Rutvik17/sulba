import json
import re
import struct

FILE = "data/model.safetensors"
# GPT-2's four sizes as (width, layers, heads), from the hparams.json OpenAI published with
# each, and the width of every one of their heads.
SIZES = {
    "small": (768, 12, 12),
    "medium": (1024, 24, 16),
    "large": (1280, 36, 20),
    "xl": (1600, 48, 25),
}
HEAD = 64


def figures():
    with open(FILE, "rb") as file:
        (size,) = struct.unpack("<Q", file.read(8))
        header = json.loads(file.read(size))
    blocks = {int(name.split(".")[1]) for name in header if re.match(r"h\.\d+\.", name)}
    width = header["wte.weight"]["shape"][1]
    assert (width, len(blocks)) == SIZES["small"][:2]
    found = {"head": str(HEAD)}
    for name, (width, layers, heads) in SIZES.items():
        assert width == heads * HEAD
        found |= {
            f"{name}_width": f"{width:,}",
            f"{name}_layers": str(layers),
            f"{name}_heads": str(heads),
        }
    return found
