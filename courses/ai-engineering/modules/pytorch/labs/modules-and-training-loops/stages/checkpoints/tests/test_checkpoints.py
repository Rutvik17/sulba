import pytest
import torch
import torch.nn.functional as F

from checkpoints import resume, save, train_epoch
from data import batches, sets
from reader import Reader

LR, MOMENTUM = 0.05, 0.9


def started(seed):
    """A reader, an optimizer and batches, as the office starts a run from seed."""
    train, _, _ = sets("data/digits.csv")
    torch.manual_seed(seed)
    reader = Reader(train.pixels)
    optimizer = torch.optim.SGD(reader.parameters(), lr=LR, momentum=MOMENTUM)
    return reader, optimizer, batches(train, seed)


def same_state(found, expected):
    return found.keys() == expected.keys() and all(
        torch.equal(found[name], expected[name]) for name in expected
    )


def same_optimizer(found, expected):
    found, expected = found.state_dict(), expected.state_dict()
    if found["param_groups"] != expected["param_groups"]:
        return False
    if found["state"].keys() != expected["state"].keys():
        return False
    return all(
        torch.equal(found["state"][key]["momentum_buffer"], state["momentum_buffer"])
        for key, state in expected["state"].items()
    )


@pytest.mark.id("tst_7rq6rj")
def test_train_epoch():
    """An epoch of steps, in training mode"""
    reader, optimizer, loader = started(0)
    office, office_optimizer, office_loader = started(0)
    reader.eval()
    loss = train_epoch(reader, optimizer, loader)
    total = 0.0
    for X, digits in office_loader:
        office_optimizer.zero_grad()
        batch_loss = F.cross_entropy(office(X), digits)
        batch_loss.backward()
        office_optimizer.step()
        total += batch_loss.item() * len(digits)
    assert reader.training
    assert loss == pytest.approx(total / len(loader.dataset), rel=1e-12)
    state = reader.state_dict()
    for name, tensor in office.state_dict().items():
        assert torch.allclose(state[name], tensor, rtol=1e-9, atol=1e-12), name


@pytest.mark.id("tst_sthd4s")
def test_checkpoint_loads(tmp_path):
    """A checkpoint torch.load reads with its defaults"""
    reader, optimizer, loader = started(0)
    train_epoch(reader, optimizer, loader)
    path = tmp_path / "run.pt"
    save(path, reader, optimizer, loader, 1)
    torch.load(path, weights_only=True)


@pytest.mark.id("tst_c0cn9x")
def test_resume(tmp_path):
    """A saved run, loaded into new objects"""
    reader, optimizer, loader = started(0)
    for _ in range(2):
        train_epoch(reader, optimizer, loader)
    path = tmp_path / "run.pt"
    save(path, reader, optimizer, loader, 2)
    fresh, fresh_optimizer, fresh_loader = started(1)
    assert resume(path, fresh, fresh_optimizer, fresh_loader) == 2
    assert same_state(fresh.state_dict(), reader.state_dict())
    assert same_optimizer(fresh_optimizer, optimizer)
    assert torch.equal(fresh_loader.generator.get_state(), loader.generator.get_state())


@pytest.mark.id("tst_1fut1t")
def test_picks_up(tmp_path):
    """A run stopped and picked up ends as if it never stopped"""
    straight = started(0)
    for _ in range(3):
        train_epoch(*straight)
    stopped = started(0)
    train_epoch(*stopped)
    path = tmp_path / "run.pt"
    save(path, *stopped, 1)
    # Picked up as a new process would, from objects of its own.
    picked = started(2)
    for _ in range(resume(path, *picked), 3):
        train_epoch(*picked)
    assert same_state(picked[0].state_dict(), straight[0].state_dict())
    assert same_optimizer(picked[1], straight[1])
