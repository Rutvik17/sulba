import io
import zipfile
from collections import Counter
from pathlib import PurePosixPath

import numpy as np
import pytest
import torch
from PIL import Image

from tiles import kinds, read, split

ARCHIVE = "data/EuroSAT_RGB.zip"


def listed(archive=ARCHIVE):
    """The zip's tiles in the order it lists them."""
    with zipfile.ZipFile(archive) as zip_file:
        return [name for name in zip_file.namelist() if name.endswith(".jpg")]


def kind(name):
    return PurePosixPath(name).parent.name


def jpeg(image):
    out = io.BytesIO()
    image.save(out, "JPEG")
    return out.getvalue()


def zipped(path, files):
    """A zip at path of files, a dict of each name and its bytes, listed in its order."""
    with zipfile.ZipFile(path, "w") as zip_file:
        for name, data in files.items():
            zip_file.writestr(name, data)
    return path


def plain(parts):
    return [(list(names), numbers.tolist()) for names, numbers in parts]


@pytest.mark.id("tst_rtg4wb")
def test_kinds():
    """The kinds, sorted"""
    assert list(kinds()) == sorted({kind(name) for name in listed()})


@pytest.mark.id("tst_ri0yy0")
def test_read():
    """The tiles named, as Pillow decodes them, channels first"""
    names = listed()[::2_700]
    with zipfile.ZipFile(ARCHIVE) as zip_file:
        decoded = [
            np.asarray(Image.open(io.BytesIO(zip_file.read(name))).convert("RGB"))
            for name in names
        ]
    tiles = read(names)
    assert tiles.dtype == torch.uint8 and tiles.shape == (len(names), 3, 64, 64)
    assert torch.equal(tiles, torch.from_numpy(np.stack(decoded)).permute(0, 3, 1, 2))


@pytest.mark.id("tst_ffy0s5")
def test_grey(tmp_path):
    """A tile in greys has three equal channels"""
    data = jpeg(Image.fromarray(np.tile(np.arange(0, 256, 4, dtype=np.uint8), (64, 1))))
    archive = zipped(tmp_path / "grey.zip", {"Forest/Forest_1.jpg": data})
    greys = torch.from_numpy(np.asarray(Image.open(io.BytesIO(data))))
    tiles = read(["Forest/Forest_1.jpg"], archive)
    assert tiles.shape == (1, 3, 64, 64)
    assert all(torch.equal(channel, greys) for channel in tiles[0])


@pytest.mark.id("tst_cectds")
def test_other_sizes(tmp_path):
    """A tile of another size is refused"""
    for size in ((32, 32), (64, 48)):
        tile = {"Forest/Forest_1.jpg": jpeg(Image.new("RGB", size))}
        with pytest.raises(ValueError):
            read(["Forest/Forest_1.jpg"], zipped(tmp_path / f"{size[1]}.zip", tile))


@pytest.mark.id("tst_bpfves")
def test_split():
    """Each kind's tiles in both parts, which share none"""
    every = kinds()
    tiles = set(listed())
    parts = split(20, 100, seed=0)
    for (names, numbers), count in zip(parts, (20, 100), strict=True):
        assert numbers.dtype == torch.int64
        assert numbers.tolist() == [every.index(kind(name)) for name in names]
        assert Counter(kind(name) for name in names) == dict.fromkeys(every, count)
        assert len(set(names)) == len(names) and set(names) <= tiles
    (learn, _), (check, _) = parts
    assert not set(learn) & set(check)


@pytest.mark.id("tst_fs920i")
def test_seeded():
    """The same seed gives the same parts, and another seed others"""
    first = plain(split(5, 5, seed=1))
    assert plain(split(5, 5, seed=1)) == first
    assert plain(split(5, 5, seed=2)) != first


@pytest.mark.id("tst_szpjtg")
def test_any_order(tmp_path):
    """The same parts from a zip that lists its tiles in another order"""
    names = sorted(listed())
    chosen = [
        name
        for each in sorted({kind(name) for name in names})
        for name in [name for name in names if kind(name) == each][:6]
    ]
    with zipfile.ZipFile(ARCHIVE) as zip_file:
        files = {name: zip_file.read(name) for name in chosen}
    forward = zipped(tmp_path / "forward.zip", dict(sorted(files.items())))
    backward = zipped(
        tmp_path / "backward.zip", dict(sorted(files.items(), reverse=True))
    )
    assert plain(split(2, 3, 7, forward)) == plain(split(2, 3, 7, backward))


@pytest.mark.id("tst_bacgvs")
def test_too_few():
    """A kind with too few tiles is refused"""
    fewest = min(Counter(kind(name) for name in listed()).values())
    split(fewest // 2, fewest - fewest // 2, seed=0)
    with pytest.raises(ValueError):
        split(fewest // 2, fewest - fewest // 2 + 1, seed=0)
