import pytest
import torch
import torch.nn.functional as F
from torch.optim.optimizer import register_optimizer_step_post_hook

from data import batches, sets
from reader import Reader
from trainer import resume, run

PATH = "data/digits.csv"
LR, MOMENTUM = 0.05, 0.9
RTOL, ATOL = 1e-10, 1e-12


def started(train, seed=0):
    """A reader, an optimizer and batches as the office starts a run from seed."""
    torch.manual_seed(seed)
    reader = Reader(train.pixels)
    optimizer = torch.optim.SGD(reader.parameters(), lr=LR, momentum=MOMENTUM)
    return reader, optimizer, batches(train, seed)


def trained(train, epochs):
    """The office's run from seed 0 after epochs epochs of training, with no validation."""
    reader, optimizer, loader = started(train)
    for _ in range(epochs):
        reader.train()
        for X, y in loader:
            optimizer.zero_grad()
            F.cross_entropy(reader(X), y).backward()
            optimizer.step()
    return reader, optimizer, loader


def close(found, expected):
    if not found.is_floating_point():
        return torch.equal(found, expected)
    return torch.allclose(found, expected, rtol=RTOL, atol=ATOL)


@pytest.mark.id("tst_on8trn")
def test_validation_changes_nothing(tmp_path):
    """Validating leaves the reader as its training left it"""
    train, validation, _ = sets(PATH)
    reader, _ = run(tmp_path / "run.pt", train, validation, epochs=2)
    expected = trained(train, 2)[0].state_dict()
    found = reader.state_dict()
    assert all(close(found[name], tensor) for name, tensor in expected.items())


@pytest.mark.id("tst_zoe2n3")
def test_momentum_picked_up(tmp_path):
    """A run picked up keeps its momentum"""
    train, validation, _ = sets(PATH)
    path = tmp_path / "run.pt"
    run(path, train, validation, epochs=1)
    reader, optimizer, loader = started(train, seed=1)
    resume(path, reader, optimizer, loader)
    found = optimizer.state_dict()["state"]
    expected = trained(train, 1)[1].state_dict()["state"]
    assert found.keys() == expected.keys()
    assert all(
        close(found[key]["momentum_buffer"], state["momentum_buffer"])
        for key, state in expected.items()
    )


@pytest.mark.id("tst_tiyhl3")
def test_order_picked_up(tmp_path):
    """A run picked up deals its batches in the order it would have"""
    train, validation, _ = sets(PATH)
    path = tmp_path / "run.pt"
    run(path, train, validation, epochs=1)
    reader, optimizer, loader = started(train)
    resume(path, reader, optimizer, loader)
    expected = trained(train, 1)[2]
    assert all(
        torch.equal(found[0], batch[0])
        for found, batch in zip(loader, expected, strict=True)
    )


@pytest.mark.id("tst_5lgmx3")
def test_epochs_picked_up(tmp_path):
    """A run stopped after an epoch trains as many epochs as one that didn't stop"""
    train, validation, _ = sets(PATH)
    path = tmp_path / "run.pt"
    steps = []
    hook = register_optimizer_step_post_hook(
        lambda optimizer, args, kwargs: steps.append(optimizer)
    )
    try:
        run(path, train, validation, epochs=1)
        run(path, train, validation, epochs=3)
    finally:
        hook.remove()
    assert len(steps) == 3 * len(batches(train, 0))
