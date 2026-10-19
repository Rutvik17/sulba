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
# Labelled tiles of each kind, fewer of them, test tiles of each kind, and the split's seed, as
# the stage's split picks them.
LABELLED, FEWER, TEST, SEED = 20, 5, 100, 0
SIDE, DECAY = 112, 1e-3
# A small convolutional network trained from nothing on the labelled tiles, for this many
# epochs, is right on fewer than this share of the test tiles. Its training in float64 drifts
# a little from one machine to another, so the stage gives the share it stays below.
EPOCHS, BOUND = 20, 0.65
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
    """The kinds, and the labelled and test tiles with their kinds' numbers, as the stage's
    split picks them."""
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
    return kinds, learn, test


def read(named):
    with zipfile.ZipFile(ARCHIVE) as zip_file:
        tiles = [
            np.asarray(Image.open(io.BytesIO(zip_file.read(name))).convert("RGB"))
            for name, _ in named
        ]
    numbers = torch.tensor([number for _, number in named])
    return torch.from_numpy(np.stack(tiles)).permute(0, 3, 1, 2), numbers


def features(weights, tiles):
    found = []
    mean, std = torch.tensor(MEAN).view(1, 3, 1, 1), torch.tensor(STD).view(1, 3, 1, 1)
    with torch.no_grad():
        for part in tiles.split(100):
            images = F.interpolate(
                part.float() / 255, size=(SIDE, SIDE), mode="bicubic"
            )
            found.append(class_tokens(weights, (images - mean) / std))
    return torch.cat(found).to(torch.float64)


def probe(rows, numbers):
    """The scores of the stage's probe, fitted to rows."""
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


def right(scores, numbers):
    top = scores.topk(2, dim=1).values
    assert (top[:, 0] - top[:, 1]).min() > GAP
    return (scores.argmax(1) == numbers).to(torch.float64).mean().item()


def from_nothing(tiles, numbers, tested, tested_numbers):
    """The share of the test tiles a small convolutional network trained from nothing on the
    labelled tiles gives right."""

    def block(inputs, outputs):
        return [
            nn.Conv2d(inputs, outputs, 3, padding=1, bias=False, dtype=torch.float64),
            nn.BatchNorm2d(outputs, dtype=torch.float64),
            nn.ReLU(),
            nn.MaxPool2d(2),
        ]

    images, test_images = tiles.to(torch.float64) / 255, tested.to(torch.float64) / 255
    mean = images.mean((0, 2, 3), keepdim=True)
    std = images.std((0, 2, 3), keepdim=True)
    torch.manual_seed(SEED)
    net = nn.Sequential(
        *block(3, 16),
        *block(16, 32),
        *block(32, 64),
        nn.Flatten(),
        nn.Linear(64 * 8 * 8, 10, dtype=torch.float64),
    )
    optimizer = torch.optim.Adam(net.parameters(), lr=1e-3)
    generator = torch.Generator().manual_seed(SEED)
    for _ in range(EPOCHS):
        net.train()
        for batch in torch.randperm(len(numbers), generator=generator).split(32):
            x = (images[batch] - mean) / std
            flip = torch.rand(len(batch), generator=generator) < 0.5
            x = torch.where(flip.view(-1, 1, 1, 1), x.flip(3), x)
            loss = F.cross_entropy(net(x), numbers[batch])
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
    net.eval()
    with torch.no_grad():
        given = net((test_images - mean) / std).argmax(1)
    return (given == tested_numbers).to(torch.float64).mean().item()


def figures():
    kinds, learn, test = split()
    weights = torch.load(CHECKPOINT, map_location="cpu", weights_only=True)
    tiles, numbers = read(learn)
    tested, tested_numbers = read(test)
    rows, rows_tested = features(weights, tiles), features(weights, tested)
    scores = probe(rows, numbers)(rows_tested)
    share = right(scores, tested_numbers)
    few = torch.cat(
        [torch.arange(k * LABELLED, k * LABELLED + FEWER) for k in range(10)]
    )
    fewer = right(probe(rows[few], numbers[few])(rows_tested), tested_numbers)
    assert from_nothing(tiles, numbers, tested, tested_numbers) < BOUND
    given = scores.argmax(1)
    counts = torch.bincount(tested_numbers * 10 + given, minlength=100).reshape(10, 10)
    counts.fill_diagonal_(0)
    worst = counts.flatten().topk(2).values
    assert worst[0] > worst[1]
    kind, taken = divmod(counts.argmax().item(), 10)
    width = rows.shape[1]
    error = math.sqrt(share * (1 - share) / len(test))
    return {
        "labelled": f"{LABELLED}",
        "labelled_total": f"{len(learn):,}",
        "tested": f"{len(test):,}",
        "per_test": f"{TEST}",
        "accuracy": f"{share:.1%}",
        "error": f"{100 * error:.1f} points",
        "twice": f"{200 * error:.1f} points",
        "fewer": f"{FEWER}",
        "fewer_accuracy": f"{fewer:.1%}",
        "epochs": f"{EPOCHS}",
        "bound": f"{BOUND:.0%}",
        "parameters": f"{width * 10 + 10:,}",
        "width": f"{width}",
        "confused": kinds[kind],
        "confused_as": kinds[taken],
        "confused_count": f"{counts[kind, taken].item()}",
    }
