import math
import os

import torch

CHECKPOINT = "data/dinov2_vits14_pretrain.pth"
# DINOv2's README: "The models were pretrained on a dataset of 142 M images without using any
# labels or annotations."
IMAGES = 142
# The side the lab resizes tiles to, and a larger one.
SIDE, LARGE = 112, 224


def multiply_adds(side, patch, width, depth):
    """A ViT's multiply-adds for an image: the patches' projection, then in each block the
    queries, keys and values, the attention's two products, its projection and the MLP."""
    tokens = (side // patch) ** 2 + 1
    project = (tokens - 1) * width * 3 * patch * patch
    attention = 3 * tokens * width * width + 2 * tokens * tokens * width
    block = attention + tokens * width * width + 2 * tokens * width * 4 * width
    return project + depth * block


def figures():
    weights = torch.load(CHECKPOINT, map_location="cpu", weights_only=True)
    parameters = sum(weight.numel() for weight in weights.values())
    width, _, patch, _ = weights["patch_embed.proj.weight"].shape
    grid = math.isqrt(weights["pos_embed"].shape[1] - 1)
    depth = len({name.split(".")[1] for name in weights if name.startswith("blocks.")})
    assert all(weight.dtype == torch.float32 for weight in weights.values())
    patches = (SIDE // patch) ** 2
    return {
        "images": f"{IMAGES} million",
        "weights": f"{len(weights)}",
        "parameters": f"{parameters:,}",
        "float_mb": f"{4 * parameters / 1e6:.1f} MB",
        "file_mb": f"{os.path.getsize(CHECKPOINT) / 1e6:.1f} MB",
        "width": f"{width}",
        "depth": f"{depth}",
        "patch": f"{patch}",
        "grid": f"{grid}",
        "trained": f"{grid * patch}",
        "side": f"{SIDE}",
        "patches": f"{patches}",
        "tokens": f"{patches + 1}",
        "large": f"{LARGE}",
        "macs_side": f"{multiply_adds(SIDE, patch, width, depth) / 1e9:.2f} billion",
        "macs_large": f"{multiply_adds(LARGE, patch, width, depth) / 1e9:.2f} billion",
    }
