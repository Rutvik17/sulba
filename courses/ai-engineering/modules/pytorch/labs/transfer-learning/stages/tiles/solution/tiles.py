"""The survey's tiles and their kinds of land use, read from EuroSAT's zip."""

import io
import random
import zipfile
from pathlib import PurePosixPath

import numpy as np
import torch
from PIL import Image

# The zip the first run fetched, which holds each tile as a JPEG in its kind's folder.
ARCHIVE = "data/EuroSAT_RGB.zip"
# A tile's side in pixels.
SIDE = 64


def tile_names(archive):
    """The names of the zip's tiles, sorted."""
    with zipfile.ZipFile(archive) as zip_file:
        return sorted(name for name in zip_file.namelist() if name.endswith(".jpg"))


def kind_of(name):
    """The kind of the tile at name: the name of its folder."""
    return PurePosixPath(name).parent.name


def kinds(archive=ARCHIVE):
    """The kinds of land use: the names of the folders that hold the zip's tiles, sorted."""
    return tuple(sorted({kind_of(name) for name in tile_names(archive)}))


def read(names, archive=ARCHIVE):
    """The tiles named, as uint8 (N, 3, SIDE, SIDE) in red, green and blue."""
    tiles = []
    with zipfile.ZipFile(archive) as zip_file:
        for name in names:
            with Image.open(io.BytesIO(zip_file.read(name))) as image:
                if image.size != (SIDE, SIDE):
                    raise ValueError(
                        f"{name} is {image.width} by {image.height} pixels."
                    )
                tiles.append(np.asarray(image.convert("RGB")))
    return torch.from_numpy(np.stack(tiles)).permute(0, 3, 1, 2).contiguous()


def split(labelled, test, seed, archive=ARCHIVE):
    """labelled tiles of each kind to learn from and test others of each kind to test with,
    picked at random from seed, each part as its tiles' names and their kinds' numbers as
    int64 (N,)."""
    every = kinds(archive)
    by_kind = {kind: [] for kind in every}
    for name in tile_names(archive):
        by_kind[kind_of(name)].append(name)
    pick = random.Random(seed)
    learn, check = [], []
    for kind in every:
        if len(by_kind[kind]) < labelled + test:
            raise ValueError(
                f"{kind} has {len(by_kind[kind])} tiles, too few to split."
            )
        chosen = pick.sample(by_kind[kind], labelled + test)
        learn += chosen[:labelled]
        check += chosen[labelled:]
    return numbered(learn, every), numbered(check, every)


def numbered(names, every):
    """The names, with their kinds' numbers in every as int64 (N,)."""
    numbers = [every.index(kind_of(name)) for name in names]
    return names, torch.tensor(numbers, dtype=torch.int64)
