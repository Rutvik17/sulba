import re

import numpy as np
import pytest
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold

from features import stays
from model import make_chosen, out_of_fold
from report import write_up
from train import SHARE, train

SECTIONS = [
    "# The readmission service",
    "## What it answers",
    "## How well it ranks",
    "## How far its probabilities hold",
    "## The calls",
    "## What it doesn't know",
]


@pytest.fixture(scope="module")
def written(tmp_path_factory):
    """The write-up for the stays among the extract's first 2,000 encounters, with what train
    gives for them and their out-of-fold probabilities."""
    path = tmp_path_factory.mktemp("extract") / "encounters.csv"
    with open("data/encounters.csv") as extract:
        path.write_text("".join(next(extract) for _ in range(2001)))
    table = stays(path)
    trained = train(path)
    probabilities = out_of_fold(table, make_chosen)
    return table, trained, probabilities, write_up(table, trained, probabilities)


def section(text, heading):
    """The text under heading, up to the next heading."""
    start = text.index(heading + "\n") + len(heading) + 1
    following = text.find("\n#", start)
    return text[start : following if following >= 0 else len(text)]


def numbers(text):
    """The text with its line breaks as spaces, to find a number however it's wrapped."""
    return re.sub(r"\s+", " ", text)


@pytest.mark.id("tst_b13w7p")
def test_sections(written):
    """Has each section, in order"""
    text = written[3]
    places = [text.find(heading + "\n") for heading in SECTIONS]
    assert -1 not in places, [h for h, p in zip(SECTIONS, places, strict=True) if p < 0]
    assert places == sorted(places)


@pytest.mark.id("tst_bn9y1g")
def test_what_it_answers(written):
    """Gives the stays it learned from and the share readmitted"""
    table, _, _, text = written
    found = numbers(section(text, "## What it answers"))
    assert f"{len(table):,}" in found
    assert f"{table['readmitted'].mean():.1%}" in found


@pytest.mark.id("tst_17gkp0")
def test_how_well_it_ranks(written):
    """Gives the mean AUC over the folds and its standard error"""
    table, _, probabilities, text = written
    y = table["readmitted"].to_numpy()
    folds = StratifiedKFold(5, shuffle=True, random_state=0).split(table, y)
    aucs = [roc_auc_score(y[test], probabilities[test]) for _, test in folds]
    error = np.std(aucs, ddof=1) / np.sqrt(len(aucs))
    found = numbers(section(text, "## How well it ranks"))
    assert f"{np.mean(aucs):.3f} ± {error:.3f}" in found


@pytest.mark.id("tst_v3el91")
def test_how_far_its_probabilities_hold(written):
    """Gives the readmissions expected and found, and the top tenth's probability and share"""
    table, _, probabilities, text = written
    y = table["readmitted"].to_numpy()
    top = probabilities >= np.quantile(probabilities, 0.9)
    found = numbers(section(text, "## How far its probabilities hold"))
    assert f"{probabilities.sum():,.0f}" in found
    assert f"{int(y.sum()):,}" in found
    assert f"{probabilities[top].mean():.1%}" in found
    assert f"{y[top].mean():.1%}" in found


@pytest.mark.id("tst_u2ht4n")
def test_the_calls(written):
    """Gives the threshold, the share called, and the recall and precision there"""
    _, trained, _, text = written
    found = numbers(section(text, "## The calls"))
    assert f"{trained['threshold']:.3f}" in found
    assert f"{SHARE:.0%}" in found
    assert f"{trained['recall']:.1%}" in found
    assert f"{trained['precision']:.1%}" in found


@pytest.mark.id("tst_57r48c")
def test_what_it_doesnt_know(written):
    """Says what it doesn't know"""
    said = section(written[3], "## What it doesn't know").strip()
    assert said.count(".") >= 2
