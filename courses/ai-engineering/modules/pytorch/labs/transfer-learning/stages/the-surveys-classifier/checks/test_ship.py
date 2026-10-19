import functools
import random
import zipfile
from pathlib import PurePosixPath

import pytest
import torch
from torch.utils.flop_counter import FlopCounterMode, sdpa_flop_count

from survey import classify, train
from tiles import read

ARCHIVE = "data/EuroSAT_RGB.zip"
# The survey's labelled tiles and test tiles of each kind, the seed it picks them with, its
# target and its budget of multiply-adds a tile.
LABELLED, TEST, SEED = 20, 50, 7
TARGET, BUDGET = 0.87, 12e9


def attention(query, key, value, *args, out_shape=None, **kwargs):
    """The floating-point operations of attention's two products, which the counter leaves
    out on the CPU."""
    return sdpa_flop_count(query, key, value)


ATTENTION = {torch.ops.aten._scaled_dot_product_flash_attention_for_cpu: attention}


@functools.cache
def survey():
    """The survey's labelled and test tiles, with their kinds' numbers."""
    with zipfile.ZipFile(ARCHIVE) as zip_file:
        names = sorted(name for name in zip_file.namelist() if name.endswith(".jpg"))
    kinds = sorted({PurePosixPath(name).parent.name for name in names})
    pick = random.Random(SEED)
    learn, test = [], []
    for kind in kinds:
        own = [name for name in names if PurePosixPath(name).parent.name == kind]
        chosen = pick.sample(own, LABELLED + TEST)
        learn += chosen[:LABELLED]
        test += chosen[LABELLED:]
    numbers = torch.arange(len(kinds))
    return (
        (read(learn), numbers.repeat_interleave(LABELLED)),
        (read(test), numbers.repeat_interleave(TEST)),
    )


@functools.cache
def trained():
    (tiles, kinds), _ = survey()
    return train(tiles, kinds)


@pytest.mark.id("tst_63th8l")
def test_target(record_property):
    """The survey's share of the test tiles"""
    _, (tiles, kinds) = survey()
    right = int((classify(trained(), tiles) == kinds).sum())
    record_property(
        "note", f"It gave {right} of the {len(kinds)} test tiles their kinds."
    )
    assert right >= TARGET * len(kinds)


@pytest.mark.id("tst_flghe9")
def test_budget(record_property):
    """Within the survey's multiply-adds a tile"""
    classifier = trained()
    _, (tiles, _) = survey()
    with FlopCounterMode(display=False, custom_mapping=ATTENTION) as counter:
        classify(classifier, tiles[:4])
    count = counter.get_total_flops() / 2 / 4
    record_property("note", f"It takes {count / 1e9:.2f} billion multiply-adds a tile.")
    assert count <= BUDGET


@pytest.mark.id("tst_6vo9ig")
def test_same():
    """The same tiles make the same classifier"""
    (tiles, kinds), (tested, _) = survey()
    few = torch.cat([torch.arange(k * LABELLED, k * LABELLED + 5) for k in range(10)])
    first = classify(train(tiles[few], kinds[few]), tested[::25])
    again = classify(train(tiles[few], kinds[few]), tested[::25])
    assert torch.equal(first, again)


@pytest.mark.id("tst_ky628h")
def test_alone():
    """A tile classified alone as among others"""
    classifier = trained()
    _, (tiles, _) = survey()
    some = tiles[::50]
    together = classify(classifier, some)
    alone = torch.cat([classify(classifier, some[i : i + 1]) for i in range(len(some))])
    assert torch.equal(alone, together)
