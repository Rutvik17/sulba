# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# Licensed under the Apache License, Version 2.0, which the lab's page gives in full, and
# which is at https://www.apache.org/licenses/LICENSE-2.0.
#
# References:
#   https://github.com/facebookresearch/dino/blob/main/vision_transformer.py
#   https://github.com/rwightman/pytorch-image-models/tree/master/timm/models/vision_transformer.py
#
# Changed from DINOv2's dinov2/models/vision_transformer.py and dinov2/layers, at commit
# 7764ea0f912e53c92e82eb78a2a1631e92725fc8: ViT-S/14's backbone alone, in one file, with
# tokens() to give every token. load, prepare and features, after DinoViT, aren't DINOv2's.
"""DINOv2's ViT-S/14, which loads Meta's dinov2_vits14_pretrain.pth as it is, and the
features it gives the survey's tiles."""

import math

import torch
import torch.nn.functional as F
from torch import nn


class PatchEmbed(nn.Module):
    """Cuts an image into square patches and maps each to a vector."""

    def __init__(self, patch_size, embed_dim):
        super().__init__()
        self.patch_size = patch_size
        self.proj = nn.Conv2d(3, embed_dim, kernel_size=patch_size, stride=patch_size)

    def forward(self, x):
        _, _, height, width = x.shape
        patch = self.patch_size
        assert height % patch == 0, f"Height {height} isn't a multiple of {patch}"
        assert width % patch == 0, f"Width {width} isn't a multiple of {patch}"
        return self.proj(x).flatten(2).transpose(1, 2)


class Attention(nn.Module):
    def __init__(self, dim, num_heads):
        super().__init__()
        self.num_heads = num_heads
        self.qkv = nn.Linear(dim, dim * 3)
        self.proj = nn.Linear(dim, dim)

    def forward(self, x):
        batch, tokens, dim = x.shape
        qkv = self.qkv(x).reshape(
            batch, tokens, 3, self.num_heads, dim // self.num_heads
        )
        q, k, v = (t.transpose(1, 2) for t in qkv.unbind(2))
        x = F.scaled_dot_product_attention(q, k, v)
        return self.proj(x.transpose(1, 2).reshape(batch, tokens, dim))


class Mlp(nn.Module):
    def __init__(self, dim, hidden):
        super().__init__()
        self.fc1 = nn.Linear(dim, hidden)
        self.act = nn.GELU()
        self.fc2 = nn.Linear(hidden, dim)

    def forward(self, x):
        return self.fc2(self.act(self.fc1(x)))


class LayerScale(nn.Module):
    def __init__(self, dim):
        super().__init__()
        self.gamma = nn.Parameter(torch.ones(dim))

    def forward(self, x):
        return x * self.gamma


class Block(nn.Module):
    def __init__(self, dim, num_heads):
        super().__init__()
        self.norm1 = nn.LayerNorm(dim, eps=1e-6)
        self.attn = Attention(dim, num_heads)
        self.ls1 = LayerScale(dim)
        self.norm2 = nn.LayerNorm(dim, eps=1e-6)
        self.mlp = Mlp(dim, 4 * dim)
        self.ls2 = LayerScale(dim)

    def forward(self, x):
        x = x + self.ls1(self.attn(self.norm1(x)))
        return x + self.ls2(self.mlp(self.norm2(x)))


class DinoViT(nn.Module):
    """ViT-S/14: 12 blocks of 384 features with 6 heads, and position embeddings for images
    of 518 by 518 pixels, 37 by 37 patches of 14 by 14."""

    def __init__(self, dim=384, depth=12, num_heads=6, patch_size=14, grid=37):
        super().__init__()
        self.patch_size = patch_size
        self.patch_embed = PatchEmbed(patch_size, dim)
        self.cls_token = nn.Parameter(torch.zeros(1, 1, dim))
        self.pos_embed = nn.Parameter(torch.zeros(1, grid * grid + 1, dim))
        self.blocks = nn.ModuleList(Block(dim, num_heads) for _ in range(depth))
        self.norm = nn.LayerNorm(dim, eps=1e-6)
        # Masked patches in DINOv2's training; kept so the checkpoint loads as it is.
        self.mask_token = nn.Parameter(torch.zeros(1, dim))

    def positions(self, height, width):
        """The position embeddings, resized from 37 by 37 patches to the image's patches as
        DINOv2 resizes them: bicubic, in float32, with its scale factors offset by 0.1."""
        pos_embed = self.pos_embed.float()
        grid = math.isqrt(pos_embed.shape[1] - 1)
        rows, columns = height // self.patch_size, width // self.patch_size
        if (rows, columns) == (grid, grid):
            return self.pos_embed
        patches = pos_embed[:, 1:].reshape(1, grid, grid, -1).permute(0, 3, 1, 2)
        patches = F.interpolate(
            patches,
            scale_factor=((rows + 0.1) / grid, (columns + 0.1) / grid),
            mode="bicubic",
            antialias=False,
        )
        patches = patches.permute(0, 2, 3, 1).reshape(1, rows * columns, -1)
        return torch.cat((pos_embed[:, :1], patches), dim=1).to(self.pos_embed.dtype)

    def tokens(self, images):
        """Every token after the last norm, (N, 1 + patches, dim): the class token, then
        each patch's, row by row."""
        _, _, height, width = images.shape
        x = self.patch_embed(images)
        x = torch.cat((self.cls_token.expand(x.shape[0], -1, -1), x), dim=1)
        x = x + self.positions(height, width)
        for block in self.blocks:
            x = block(x)
        return self.norm(x)

    def forward(self, images):
        """The class token's features after the last norm, (N, dim)."""
        return self.tokens(images)[:, 0]


# The checkpoint the first run fetched.
CHECKPOINT = "data/dinov2_vits14_pretrain.pth"
# The side of the backbone's patches, in pixels.
PATCH = 14
# The mean and standard deviation of each channel in ImageNet's images, which DINOv2's
# transforms normalize images with.
MEAN = (0.485, 0.456, 0.406)
STD = (0.229, 0.224, 0.225)


def load(path=CHECKPOINT):
    """DinoViT with the checkpoint's weights at path, in eval mode and frozen."""
    raise NotImplementedError


def prepare(tiles, side):
    """Tiles, uint8 (N, 3, H, W), as the backbone takes them: float32 (N, 3, side, side),
    resized and normalized as DINOv2's images were."""
    raise NotImplementedError


def features(backbone, tiles, side, batch=256):
    """The backbone's features of each tile, float32 (N, dim), on the CPU: batch tiles at a
    time, on the device the backbone is on."""
    raise NotImplementedError
