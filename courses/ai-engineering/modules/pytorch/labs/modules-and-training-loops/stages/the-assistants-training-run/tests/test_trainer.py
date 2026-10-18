import pytest
import torch

from data import evaluate, sets
from trainer import run

PATH = "data/digits.csv"


@pytest.mark.id("tst_8tbdv9")
def test_reads_validation(tmp_path):
    """Three epochs read most of the validation digits"""
    train, validation, _ = sets(PATH)
    reader, losses = run(tmp_path / "run.pt", train, validation, epochs=3)
    _, right = evaluate(reader, validation)
    assert right >= 0.9 * len(validation)
    assert len(losses) == 3 and losses[-1] < losses[0]


@pytest.mark.id("tst_cbva4q")
def test_saves(tmp_path):
    """The run is saved after each epoch"""
    train, validation, _ = sets(PATH)
    path = tmp_path / "run.pt"
    run(path, train, validation, epochs=1)
    checkpoint = torch.load(path)
    assert set(checkpoint) == {"reader", "optimizer", "generator", "epochs"}


@pytest.mark.id("tst_ln8ozq")
def test_goes_on(tmp_path):
    """A second run goes on from the first instead of starting again"""
    train, validation, _ = sets(PATH)
    path = tmp_path / "run.pt"
    run(path, train, validation, epochs=2)
    reader, losses = run(path, train, validation, epochs=3)
    assert 0 < len(losses) < 3
    _, right = evaluate(reader, validation)
    assert right >= 0.9 * len(validation)
