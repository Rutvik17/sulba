"""Fine-tunes DINOv2's ViT-S/14 with a linear head on the survey's labelled tiles: the head
first, with the backbone frozen, then every layer, the backbone at a smaller rate."""

import zipfile
from pathlib import PurePosixPath

import torch
import torch.nn.functional as F
from torch import nn

from backbone import load, prepare

ARCHIVE = "data/EuroSAT_RGB.zip"
# The rates the head and the backbone learn at, and AdamW's weight decay.
HEAD_RATE, BACKBONE_RATE, DECAY = 1e-3, 1e-5, 1e-4


class Classifier(nn.Module):
    """The backbone, with a linear head that gives each kind a score from its features."""

    def __init__(self, backbone, count):
        super().__init__()
        self.backbone = backbone
        self.head = nn.Linear(backbone.norm.normalized_shape[0], count)

    def forward(self, images):
        return self.head(self.backbone(images))


def kind_names(archive=ARCHIVE):
    """The name of each kind the classifier gives, by its number."""
    with zipfile.ZipFile(archive) as zip_file:
        names = [name for name in zip_file.namelist() if name.endswith(".jpg")]
    return list(dict.fromkeys(PurePosixPath(name).parent.name for name in names))


def scores(model, tiles, side):
    """The classifier's score for each kind, for each tile."""
    with torch.no_grad():
        return model(prepare(tiles, side))


def train(model, optimizer, tiles, kinds, side, epochs, size, generator):
    """Trains the parameters optimizer holds for epochs epochs, in random batches of size
    tiles, each flipped left to right at random."""
    model.train().requires_grad_(True)
    for _ in range(epochs):
        for batch in torch.randperm(len(kinds), generator=generator).split(size):
            flip = torch.rand(len(batch), generator=generator) < 0.5
            images = torch.where(
                flip.view(-1, 1, 1, 1), tiles[batch].flip(3), tiles[batch]
            )
            images = F.interpolate(images / 255, size=(side, side), mode="bicubic")
            loss = F.cross_entropy(model(images), kinds[batch])
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
    model.eval()


def warm_up(model, tiles, kinds, side, epochs, size, generator):
    """Trains the head alone, with the backbone frozen."""
    optimizer = torch.optim.AdamW(
        model.head.parameters(), lr=HEAD_RATE, weight_decay=DECAY
    )
    train(model, optimizer, tiles, kinds, side, epochs, size, generator)


def fine_tune(model, tiles, kinds, side, epochs, size, generator):
    """Trains every layer, the backbone at its smaller rate."""
    model.requires_grad_(True)
    optimizer = torch.optim.AdamW(model.parameters(), lr=HEAD_RATE, weight_decay=DECAY)
    train(model, optimizer, tiles, kinds, side, epochs, size, generator)


def survey_classifier(tiles, kinds, side=112, warmup=5, epochs=10, size=32, seed=0):
    """A classifier for the labelled tiles and their kinds' numbers: its head warmed up for
    warmup epochs, then every layer fine-tuned for epochs, with every chance decided by
    seed."""
    torch.manual_seed(seed)
    generator = torch.Generator().manual_seed(seed)
    model = Classifier(load(), len(kind_names()))
    warm_up(model, tiles, kinds, side, warmup, size, generator)
    fine_tune(model, tiles, kinds, side, epochs, size, generator)
    return model
