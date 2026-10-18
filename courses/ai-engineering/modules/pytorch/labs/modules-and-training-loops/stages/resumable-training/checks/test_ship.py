import copy
import functools
import tempfile
from pathlib import Path

import pytest
import torch
from torch.optim.optimizer import register_optimizer_step_post_hook

from checkpoints import train_epoch
from data import batches, evaluate, sets
from reader import Reader
from run import run

PATH = "data/digits.csv"
EPOCHS, LR, MOMENTUM, TARGET = 15, 0.05, 0.9, 0.95


class Stopped(BaseException):
    """The run stopped, as when its process is killed: nothing in the run should catch it."""


@functools.cache
def straight():
    """The reader a run that never stopped returns."""
    train, validation, _ = sets(PATH)
    with tempfile.TemporaryDirectory() as folder:
        return run(Path(folder) / "run.pt", train, validation)


def same(found, expected):
    found, expected = found.state_dict(), expected.state_dict()
    return found.keys() == expected.keys() and all(
        torch.equal(found[name], tensor) for name, tensor in expected.items()
    )


class Steps:
    """Counts the optimizer steps taken while it's open."""

    def __enter__(self):
        self.count = 0
        self.hook = register_optimizer_step_post_hook(self.step)
        return self

    def step(self, optimizer, args, kwargs):
        self.count += 1

    def __exit__(self, *exception):
        self.hook.remove()


@pytest.mark.id("tst_8it14j")
def test_new_writers():
    """95% of new writers' digits"""
    _, _, test = sets(PATH)
    _, right = evaluate(straight(), test)
    assert right >= TARGET * len(test)


@pytest.mark.id("tst_ymoscm")
def test_best_epoch():
    """The state of the epoch with the lowest validation loss"""
    train, validation, _ = sets(PATH)
    torch.manual_seed(0)
    reader = Reader(train.pixels)
    optimizer = torch.optim.SGD(reader.parameters(), lr=LR, momentum=MOMENTUM)
    loader = batches(train, 0)
    best = None
    for _ in range(EPOCHS):
        train_epoch(reader, optimizer, loader)
        loss, _ = evaluate(reader, validation)
        if best is None or loss < best[0]:
            best = loss, copy.deepcopy(reader.state_dict())
    reader.load_state_dict(best[1])
    assert same(straight(), reader)


@pytest.mark.id("tst_mrs9jt")
def test_stopped(tmp_path):
    """Stopped after an epoch, it ends as if it never stopped"""
    train, validation, _ = sets(PATH)
    # Stopped before the epoch that validates best, and after it.
    for stop in (3, 13):
        path = tmp_path / f"stopped-{stop}.pt"
        run(path, train, validation, epochs=stop)
        assert same(run(path, train, validation), straight())


@pytest.mark.id("tst_36jsdo")
def test_stopped_saving(tmp_path, monkeypatch):
    """Stopped while it saves, it picks up from the last checkpoint"""
    train, validation, _ = sets(PATH)
    per_epoch = len(batches(train, 0))
    write = torch.serialization._save
    stopped = []

    def stopping(*args, **kwargs):
        # Stops the save after epoch 5 once torch.save has opened the file it writes, before
        # the checkpoint is in it, however the run calls torch.save.
        if steps.count == 5 * per_epoch and not stopped:
            stopped.append(True)
            raise Stopped
        return write(*args, **kwargs)

    path = tmp_path / "run.pt"
    with monkeypatch.context() as patch, Steps() as steps:
        patch.setattr(torch.serialization, "_save", stopping)
        with pytest.raises(Stopped):
            run(path, train, validation)
    with Steps() as steps:
        reader = run(path, train, validation)
    assert steps.count == (EPOCHS - 4) * per_epoch
    assert same(reader, straight())


@pytest.mark.id("tst_mpz0wa")
def test_reads_alone():
    """Reads a digit alone as among others"""
    _, _, test = sets(PATH)
    reader = straight()
    with torch.no_grad():
        alone = torch.cat(
            [reader(test.pixels[number : number + 1]) for number in range(20)]
        )
        among = reader(test.pixels)[:20]
    assert torch.allclose(alone, among, rtol=1e-10, atol=1e-12)
