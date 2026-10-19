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
# The assistant's rates, and the survey's fine-tuning: its labelled tiles of each kind, its
# batches, its epochs of warm-up and of fine-tuning, and the side it resizes tiles to.
HEAD_RATE, BACKBONE_RATE = 1e-3, 1e-5
LABELLED, BATCH, WARMUP, EPOCHS, SIDE = 20, 32, 5, 10, 112
# Stage 3's split and probe.
TEST, SEED, DECAY = 100, 0, 1e-3
# A probe trained on the features of unnormalized tiles is right on fewer than this share of
# the test tiles once it's given the features of normalized ones. Some of its scores stand
# too close for float32's last digits, so the stage gives the share it stays below.
BOUND = 0.7
# Features in float32 differ in their last digits from one machine to another, which moves a
# probe's scores by about a thousandth. Every test tile's two highest scores stand further
# apart than this, so each machine gives every tile the same kind.
GAP = 0.01


def class_tokens(weights, images, heads=6):
    """ViT-S/14's class token after the last norm, for images normalized as DINOv2's."""
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
    return F.layer_norm(x, (width,), w["norm.weight"], w["norm.bias"], 1e-6)[:, 0]


def split():
    """The kinds in the zip's order and sorted, and stage 3's labelled and test tiles with
    their kinds' numbers."""
    with zipfile.ZipFile(ARCHIVE) as zip_file:
        listed = [n for n in zip_file.namelist() if n.endswith(".jpg")]
    names = sorted(listed)
    folders = list(dict.fromkeys(PurePosixPath(name).parent.name for name in listed))
    kinds = sorted(folders)
    pick = random.Random(SEED)
    learn, test = [], []
    for number, kind in enumerate(kinds):
        own = [name for name in names if PurePosixPath(name).parent.name == kind]
        chosen = pick.sample(own, LABELLED + TEST)
        learn += [(name, number) for name in chosen[:LABELLED]]
        test += [(name, number) for name in chosen[LABELLED:]]
    return folders, kinds, learn, test


def read(named):
    with zipfile.ZipFile(ARCHIVE) as zip_file:
        tiles = [
            np.asarray(Image.open(io.BytesIO(zip_file.read(name))).convert("RGB"))
            for name, _ in named
        ]
    numbers = torch.tensor([number for _, number in named])
    return torch.from_numpy(np.stack(tiles)).permute(0, 3, 1, 2), numbers


def features(weights, tiles, normalized):
    found = []
    mean, std = torch.tensor(MEAN).view(1, 3, 1, 1), torch.tensor(STD).view(1, 3, 1, 1)
    with torch.no_grad():
        for part in tiles.split(100):
            images = F.interpolate(
                part.float() / 255, size=(SIDE, SIDE), mode="bicubic"
            )
            if normalized:
                images = (images - mean) / std
            found.append(class_tokens(weights, images))
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


def linear_multiply_adds(weights):
    """The multiply-adds a tile takes in the backbone's linear layers, at SIDE pixels."""
    patch = weights["patch_embed.proj.weight"].shape[-1]
    tokens = (SIDE // patch) ** 2 + 1
    linear = [
        w for name, w in weights.items() if name.startswith("blocks.") and w.dim() == 2
    ]
    return sum(tokens * w.numel() for w in linear)


def figures():
    folders, kinds, learn, test = split()
    weights = torch.load(CHECKPOINT, map_location="cpu", weights_only=True)
    median = torch.cat([w.abs().flatten() for w in weights.values()]).median().item()
    steps = EPOCHS * math.ceil(len(learn) / BATCH)
    tiles, numbers = read(learn)
    tested, tested_numbers = read(test)
    normalized = probe(features(weights, tiles, True), numbers)
    scores = normalized(features(weights, tested, True))
    top = scores.topk(2, dim=1).values
    assert (top[:, 0] - top[:, 1]).min() > GAP
    right = (scores.argmax(1) == tested_numbers).to(torch.float64).mean().item()
    unnormalized = probe(features(weights, tiles, False), numbers)
    given = unnormalized(features(weights, tested, True)).argmax(1)
    assert (given == tested_numbers).to(torch.float64).mean().item() < BOUND
    forward = linear_multiply_adds(weights)
    parameters = sum(w.numel() for w in weights.values())
    return {
        "head_rate": f"{HEAD_RATE:g}",
        "backbone_rate": f"{BACKBONE_RATE:.5f}",
        "median": f"{median:.4f}",
        "share": f"{HEAD_RATE / median:.0%}",
        "small_share": f"{BACKBONE_RATE / median:.2%}",
        "steps": f"{steps}",
        "drift": f"{steps * HEAD_RATE:g}",
        "times": f"{steps * HEAD_RATE / median:.1f}",
        "normalized": f"{right:.1%}",
        "bound": f"{BOUND:.0%}",
        "first_listed": folders[0],
        "first_sorted": kinds[0],
        "moved": f"{sum(a != b for a, b in zip(folders, kinds, strict=True))}",
        "kinds": f"{len(kinds)}",
        "side": f"{SIDE}",
        "linear_forward": f"{forward / 1e9:.2f} billion",
        "backward": f"{2 * forward / 1e9:.2f} billion",
        "warm_tiles": f"{WARMUP * len(learn):,}",
        "wasted": f"{WARMUP * len(learn) * 2 * forward / 1e12:.2f} trillion",
        "grad_mb": f"{4 * parameters / 1e6:.1f} MB",
    }
