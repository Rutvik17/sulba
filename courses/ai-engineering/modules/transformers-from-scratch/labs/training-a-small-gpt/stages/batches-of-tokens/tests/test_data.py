import pytest
import torch
import torch.nn.functional as F

from data import batches, corpus, evaluate, split
from tokenizer import encode, stories, train

FILE = "data/TinyStoriesV2-GPT4-valid.txt"


class Reader(torch.nn.Module):
    """A model that guesses each next token from the token before it, through dropout."""

    def __init__(self, vocab):
        super().__init__()
        self.table = torch.nn.Embedding(vocab, vocab)
        self.dropout = torch.nn.Dropout(0.5)

    def forward(self, tokens):
        return self.dropout(self.table(tokens))


@pytest.mark.id("tst_aqf6dh")
def test_split():
    """Every tenth story to validate with, the rest to train on"""
    told = stories(FILE)
    training, validation = split(told)
    assert len(training) == 24867 and len(validation) == 2762
    assert validation[:2] == [told[9], told[19]]
    assert training[:10] == told[:9] + [told[10]]
    assert split(["a", "b"]) == (["a", "b"], [])


@pytest.mark.id("tst_kafudx")
def test_corpus():
    """One tensor of tokens, each story followed by the separator"""
    told = stories(FILE)[:200]
    merges = train(told, 400)
    tokens = corpus(told[:3], merges)
    expected = []
    for story in told[:3]:
        expected += encode(story, merges) + [399]
    assert tokens.dtype == torch.int64
    assert tokens.tolist() == expected


def started(batch, length):
    """The start of each window of a batch of torch.arange's tokens."""
    inputs, targets = batch
    assert inputs.shape == targets.shape == (len(inputs), length)
    assert torch.equal(targets, inputs + 1)
    assert torch.equal(inputs, inputs[:, :1] + torch.arange(length))
    return inputs[:, 0].tolist()


@pytest.mark.id("tst_hjn0t2")
def test_targets():
    """Each window's targets, one token on"""
    stream = batches(torch.arange(1000), 10, 4, torch.Generator().manual_seed(0))
    for _ in range(30):
        starts = started(next(stream), 10)
        assert all(start % 10 == 0 for start in starts)


@pytest.mark.id("tst_vhznaz")
def test_passes():
    """Each pass, every window once in a new order, then the next pass"""
    # 1,000 tokens hold 99 windows of 10 with their targets: 24 batches of 4 and 3 left over.
    stream = batches(torch.arange(1000), 10, 4, torch.Generator().manual_seed(1))
    passes = [
        [start for _ in range(24) for start in started(next(stream), 10)] for _ in "ab"
    ]
    for starts in passes:
        assert len(set(starts)) == 96
        assert set(starts) <= set(range(0, 990, 10))
    assert passes[0] != passes[1]
    assert passes[0] != sorted(passes[0])


@pytest.mark.id("tst_ar2sqn")
def test_generator():
    """The same batches from the same generator"""
    first = batches(torch.arange(500), 8, 3, torch.Generator().manual_seed(2))
    again = batches(torch.arange(500), 8, 3, torch.Generator().manual_seed(2))
    other = batches(torch.arange(500), 8, 3, torch.Generator().manual_seed(3))
    seen = [next(first)[0] for _ in range(10)]
    assert all(torch.equal(each, next(again)[0]) for each in seen)
    assert not all(torch.equal(each, next(other)[0]) for each in seen)


@pytest.mark.id("tst_5twtm8")
def test_evaluate():
    """The mean loss a token, in evaluation mode, without gradients"""
    torch.manual_seed(0)
    model = Reader(50)
    tokens = torch.randint(50, (1003,))
    # 1,003 tokens hold 100 windows of 10 with their targets, read in 2 batches.
    every = tokens[: 100 * 10 + 1]
    expected = F.cross_entropy(model.table(every[:-1]), every[1:]).item()
    assert evaluate(model, tokens, 10, size=64) == pytest.approx(expected, rel=1e-6)
    assert model.training
    assert model.table.weight.grad is None
    model.eval()
    assert evaluate(model, tokens, 10, size=7) == pytest.approx(expected, rel=1e-6)
    assert not model.training
