# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# Licensed under the Apache License, Version 2.0, which the lab's page gives in full, and
# which is at https://www.apache.org/licenses/LICENSE-2.0.
#
# Changed from DINOv2's dinov2/models/vision_transformer.py and dinov2/layers, at commit
# 7764ea0f912e53c92e82eb78a2a1631e92725fc8: ViT-S/14's forward pass alone, as one function
# of the checkpoint's weights.

import io
import math
import random
import zipfile
from pathlib import PurePosixPath

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from torch import nn

ARCHIVE = "data/EuroSAT_RGB.zip"
CHECKPOINT = "data/dinov2_vits14_pretrain.pth"
MEAN, STD = (0.485, 0.456, 0.406), (0.229, 0.224, 0.225)
# The survey's labelled and test tiles of each kind, the seed it picks them with, its target
# and its budget of multiply-adds a tile, as its checks have them.
LABELLED, TEST, SEED = 20, 50, 7
TARGET, BUDGET = 0.87, 12e9
# Stage 3's side and decay, the solution's side, and the square's symmetries.
SIDE, DECAY, LARGE, VIEWS = 112, 1e-3, 224, 8
# Features in float32 differ in their last digits from one machine to another, which moves a
# probe's scores by about a thousandth. Every test tile's two highest scores stand further
# apart than this, so each machine gives every tile the same kind.
GAP = 0.01


def tokens(weights, images, heads=6):
    """ViT-S/14's tokens after the last norm, for images normalized as DINOv2's: the class
    token, then each patch's."""
    w = weights
    patch = w["patch_embed.proj.weight"].shape[-1]
    x = F.conv2d(
        images, w["patch_embed.proj.weight"], w["patch_embed.proj.bias"], stride=patch
    )
    batch, width, rows, columns = x.shape
    x = torch.cat(
        (w["cls_token"].expand(batch, -1, -1), x.flatten(2).transpose(1, 2)), dim=1
    )
    grid = math.isqrt(w["pos_embed"].shape[1] - 1)
    embedded = w["pos_embed"][:, 1:].reshape(1, grid, grid, -1).permute(0, 3, 1, 2)
    embedded = F.interpolate(
        embedded,
        scale_factor=((rows + 0.1) / grid, (columns + 0.1) / grid),
        mode="bicubic",
        antialias=False,
    )
    embedded = embedded.permute(0, 2, 3, 1).reshape(1, rows * columns, -1)
    x = x + torch.cat((w["pos_embed"][:, :1], embedded), dim=1)
    tokens = x.shape[1]
    for block in range(
        len({name.split(".")[1] for name in w if name.startswith("blocks.")})
    ):
        p = f"blocks.{block}."
        h = F.layer_norm(x, (width,), w[p + "norm1.weight"], w[p + "norm1.bias"], 1e-6)
        qkv = F.linear(h, w[p + "attn.qkv.weight"], w[p + "attn.qkv.bias"])
        q, k, v = (
            t.transpose(1, 2)
            for t in qkv.reshape(batch, tokens, 3, heads, -1).unbind(2)
        )
        h = (
            F.scaled_dot_product_attention(q, k, v)
            .transpose(1, 2)
            .reshape(batch, tokens, width)
        )
        h = F.linear(h, w[p + "attn.proj.weight"], w[p + "attn.proj.bias"])
        x = x + h * w[p + "ls1.gamma"]
        h = F.layer_norm(x, (width,), w[p + "norm2.weight"], w[p + "norm2.bias"], 1e-6)
        h = F.linear(
            F.gelu(F.linear(h, w[p + "mlp.fc1.weight"], w[p + "mlp.fc1.bias"])),
            w[p + "mlp.fc2.weight"],
            w[p + "mlp.fc2.bias"],
        )
        x = x + h * w[p + "ls2.gamma"]
    return F.layer_norm(x, (width,), w["norm.weight"], w["norm.bias"], 1e-6)


def split():
    """The survey's labelled and test tiles, with their kinds' numbers, as its checks pick
    them."""
    with zipfile.ZipFile(ARCHIVE) as zip_file:
        names = sorted(n for n in zip_file.namelist() if n.endswith(".jpg"))
    kinds = sorted({PurePosixPath(name).parent.name for name in names})
    pick = random.Random(SEED)
    learn, test = [], []
    for number, kind in enumerate(kinds):
        own = [name for name in names if PurePosixPath(name).parent.name == kind]
        chosen = pick.sample(own, LABELLED + TEST)
        learn += [(name, number) for name in chosen[:LABELLED]]
        test += [(name, number) for name in chosen[LABELLED:]]
    return learn, test


def read(named):
    with zipfile.ZipFile(ARCHIVE) as zip_file:
        tiles = [
            np.asarray(Image.open(io.BytesIO(zip_file.read(name))).convert("RGB"))
            for name, _ in named
        ]
    numbers = torch.tensor([number for _, number in named])
    return torch.from_numpy(np.stack(tiles)).permute(0, 3, 1, 2), numbers


def features(weights, tiles, side, pooled):
    """The class token of each tile, or the class token beside the mean of the patches'."""
    found = []
    mean, std = torch.tensor(MEAN).view(1, 3, 1, 1), torch.tensor(STD).view(1, 3, 1, 1)
    with torch.no_grad():
        for part in tiles.split(64):
            images = F.interpolate(
                part.float() / 255, size=(side, side), mode="bicubic"
            )
            every = tokens(weights, (images - mean) / std)
            found.append(
                torch.cat((every[:, 0], every[:, 1:].mean(1)), dim=1)
                if pooled
                else every[:, 0]
            )
    return torch.cat(found).to(torch.float64)


def probe(rows, numbers):
    """The scores of stage 3's probe, fitted to rows."""
    mean, std = rows.mean(0), rows.std(0)
    layer = nn.Linear(rows.shape[1], 10, dtype=torch.float64)
    nn.init.zeros_(layer.weight)
    nn.init.zeros_(layer.bias)
    optimizer = torch.optim.LBFGS(
        layer.parameters(),
        max_iter=1000,
        tolerance_grad=1e-9,
        tolerance_change=0,
        line_search_fn="strong_wolfe",
    )

    def closure():
        optimizer.zero_grad()
        loss = F.cross_entropy(layer((rows - mean) / std), numbers)
        loss = loss + DECAY * layer.weight.square().sum()
        loss.backward()
        return loss

    optimizer.step(closure)
    return lambda tested: layer((tested - mean) / std).detach()


def right(weights, learn, test, side, pooled):
    """The share of the test tiles a probe on the features gives their kinds."""
    (tiles, numbers), (tested, tested_numbers) = learn, test
    learned = features(weights, tiles, side, pooled)
    scores = probe(learned, numbers)(features(weights, tested, side, pooled))
    top = scores.topk(2, dim=1).values
    assert (top[:, 0] - top[:, 1]).min() > GAP
    return (scores.argmax(1) == tested_numbers).to(torch.float64).mean().item()


def multiply_adds(weights, side):
    """A tile's multiply-adds at side pixels: the patches' projection, then in each block the
    linear layers and attention's two products."""
    patch = weights["patch_embed.proj.weight"].shape[-1]
    width = weights["pos_embed"].shape[-1]
    count = (side // patch) ** 2 + 1
    linear = [
        w for name, w in weights.items() if name.startswith("blocks.") and w.dim() == 2
    ]
    depth = len({name.split(".")[1] for name in weights if name.startswith("blocks.")})
    project = (count - 1) * weights["patch_embed.proj.weight"].numel()
    return (
        project + sum(count * w.numel() for w in linear) + depth * 2 * count**2 * width
    )


def figures():
    learn, test = split()
    weights = torch.load(CHECKPOINT, map_location="cpu", weights_only=True)
    labelled, tested = read(learn), read(test)
    baseline = right(weights, labelled, tested, SIDE, pooled=False)
    solution = right(weights, labelled, tested, LARGE, pooled=True)
    assert baseline < TARGET <= solution
    patch = weights["patch_embed.proj.weight"].shape[-1]
    small, large = multiply_adds(weights, SIDE), multiply_adds(weights, LARGE)
    return {
        "labelled": f"{LABELLED}",
        "per_test": f"{TEST}",
        "tested": f"{len(test):,}",
        "target": f"{TARGET:.0%}",
        "budget": f"{BUDGET / 1e9:.0f} billion",
        "side": f"{SIDE}",
        "large": f"{LARGE}",
        "patches": f"{(SIDE // patch) ** 2}",
        "large_patches": f"{(LARGE // patch) ** 2}",
        "baseline": f"{baseline:.1%}",
        "baseline_macs": f"{small / 1e9:.2f} billion",
        "solution": f"{solution:.1%}",
        "solution_macs": f"{large / 1e9:.2f} billion",
        "views": f"{VIEWS}",
        "views_macs": f"{VIEWS * small / 1e9:.2f} billion",
    }
