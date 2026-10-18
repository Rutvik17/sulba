import numpy as np
import pytest
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader

from data import Digits, batches, evaluate, sets
from reader import Reader

PATH = "data/digits.csv"


def numbered(n):
    """n digits whose one pixel is their own number, so a batch shows which ones it holds."""
    return Digits(
        torch.arange(n, dtype=torch.float64).unsqueeze(1), torch.zeros(n).long()
    )


def epoch(loader):
    return [pixels[:, 0].long().tolist() for pixels, _ in loader]


def trained_reader(train):
    """A reader with a few steps of training behind it, so its running estimates have moved."""
    torch.manual_seed(0)
    reader = Reader(train.pixels)
    optimizer = torch.optim.SGD(reader.parameters(), lr=0.05, momentum=0.9)
    for start in range(0, 640, 64):
        rows = slice(start, start + 64)
        optimizer.zero_grad()
        F.cross_entropy(reader(train.pixels[rows]), train.digits[rows]).backward()
        optimizer.step()
    return reader


@pytest.mark.id("tst_4n14s5")
def test_sets():
    """The office's three sets"""
    table = np.loadtxt(PATH, delimiter=",", skiprows=1)
    found = sets(PATH)
    assert len(found) == 3
    for number, part in enumerate(found):
        rows = table[table[:, 0] == number]
        assert len(part) == len(rows)
        assert part.pixels.dtype == torch.float64 and part.digits.dtype == torch.int64
        assert np.array_equal(part.pixels.numpy(), rows[:, 2:])
        assert np.array_equal(part.digits.numpy(), rows[:, 1])


@pytest.mark.id("tst_jxq95n")
def test_digits():
    """A dataset of digits"""
    pixels = torch.rand(5, 64, dtype=torch.float64)
    digits = torch.tensor([3, 1, 4, 1, 5])
    dataset = Digits(pixels, digits)
    assert len(dataset) == 5
    item = dataset[2]
    assert torch.equal(item[0], pixels[2]) and int(item[1]) == 4
    X, y = next(iter(DataLoader(dataset, batch_size=5)))
    assert torch.equal(X, pixels) and torch.equal(y, digits)


@pytest.mark.id("tst_v7m791")
def test_batches():
    """Batches of 64, in a new order each epoch"""
    loader = batches(numbered(2867), 0)
    first, second = epoch(loader), epoch(loader)
    for found in (first, second):
        assert [len(batch) for batch in found] == [64] * 44 + [51]
        assert sorted(sum(found, [])) == list(range(2867))
    assert first != second


@pytest.mark.id("tst_tge01k")
def test_order():
    """The office's order from its seed, and the global generator left alone"""
    dataset = numbered(300)
    for seed in (0, 1):
        generator = torch.Generator().manual_seed(seed)
        office = DataLoader(dataset, batch_size=64, shuffle=True, generator=generator)
        loader = batches(dataset, seed)
        state = torch.get_rng_state()
        for _ in range(2):
            assert epoch(loader) == epoch(office)
        assert torch.equal(torch.get_rng_state(), state)


@pytest.mark.id("tst_ajm5i4")
def test_evaluate():
    """The validation digits read in evaluation"""
    train, validation, _ = sets(PATH)
    reader = trained_reader(train)
    reader.eval()
    with torch.no_grad():
        logits = reader(validation.pixels)
    loss = F.cross_entropy(logits, validation.digits).item()
    right = int((logits.argmax(dim=1) == validation.digits).sum())
    for mode in (True, False):
        reader.train(mode)
        state = {name: tensor.clone() for name, tensor in reader.state_dict().items()}
        found_loss, found_right = evaluate(reader, validation)
        assert found_loss == pytest.approx(loss, rel=1e-12) and found_right == right
        assert reader.training == mode
        assert all(
            torch.equal(reader.state_dict()[name], state[name]) for name in state
        )


@pytest.mark.id("tst_opf1ng")
def test_evaluate_graph():
    """Evaluation records nothing for a backward pass"""
    train, validation, _ = sets(PATH)
    reader = trained_reader(train)
    saved = []

    def pack(tensor):
        saved.append(tensor.shape)
        return tensor

    with torch.autograd.graph.saved_tensors_hooks(pack, lambda tensor: tensor):
        loss, right = evaluate(reader, validation)
    assert saved == []
    assert isinstance(loss, float) and isinstance(right, int)
