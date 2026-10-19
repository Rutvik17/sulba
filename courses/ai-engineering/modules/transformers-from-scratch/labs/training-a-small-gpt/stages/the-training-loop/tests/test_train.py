import math

import pytest
import torch
import torch.nn.functional as F

from data import batches, corpus, evaluate, split
from tokenizer import stories
from tokenizer import train as learn
from train import GPT, schedule, train, write

FILE = "data/TinyStoriesV2-GPT4-valid.txt"


def tiny(context=16, dtype=torch.float64):
    torch.manual_seed(0)
    return GPT(64, context, 32, 2, 2).to(dtype)


def fixed(count=8, length=16, size=4):
    """count batches of random tokens."""
    generator = torch.Generator().manual_seed(1)
    given = []
    for _ in range(count):
        chunk = torch.randint(64, (size, length + 1), generator=generator)
        given.append((chunk[:, :-1], chunk[:, 1:]))
    return given


def stepped(model, given, steps, peak, warmup):
    """Training as the brief sets it out, and whether clipping cut a step's gradient."""
    matrices = [param for param in model.parameters() if param.dim() >= 2]
    others = [param for param in model.parameters() if param.dim() < 2]
    optimizer = torch.optim.AdamW(
        [
            {"params": matrices, "weight_decay": 0.1},
            {"params": others, "weight_decay": 0.0},
        ],
        betas=(0.9, 0.95),
        eps=1e-8,
    )
    losses, clipped = [], False
    for step in range(steps):
        rate = schedule(step, steps, peak, warmup)
        for group in optimizer.param_groups:
            group["lr"] = rate
        inputs, targets = next(given)
        loss = F.cross_entropy(model(inputs).flatten(0, 1), targets.flatten())
        optimizer.zero_grad()
        loss.backward()
        clipped |= torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0) > 1
        optimizer.step()
        losses.append(loss.item())
    return losses, clipped


def drawn(model, tokens, count, generator, temperature=1.0):
    """The tokens write should give."""
    tokens = list(tokens)
    with torch.no_grad():
        for _ in range(count):
            logits = model(torch.tensor([tokens[-model.context :]]))[0, -1]
            chances = torch.softmax(logits / temperature, dim=-1)
            tokens.append(torch.multinomial(chances, 1, generator=generator).item())
            if tokens[-1] == model.wte.num_embeddings - 1:
                break
    return tokens


class Spare(torch.nn.Module):
    """A tiny GPT with a matrix and a vector that add nothing to its logits."""

    def __init__(self):
        super().__init__()
        self.gpt = tiny()
        self.matrix = torch.nn.Parameter(torch.ones(3, 3, dtype=torch.float64))
        self.vector = torch.nn.Parameter(torch.ones(3, dtype=torch.float64))

    def forward(self, tokens):
        return self.gpt(tokens) + 0 * (self.matrix.sum() + self.vector.sum())


class Fixed(torch.nn.Module):
    """A tiny GPT whose separator's logit is set: very low, or very high."""

    def __init__(self, separator, context=16):
        super().__init__()
        self.gpt = tiny(context, torch.float32)
        self.context, self.wte, self.separator = context, self.gpt.wte, separator

    def forward(self, tokens):
        logits = self.gpt(tokens)
        logits[..., -1] = self.separator
        return logits


@pytest.mark.id("tst_hn3vuf")
def test_schedule():
    """Up in a straight line over the warm-up, then down a cosine to a tenth"""
    peak = 1e-3
    assert schedule(0, 101, peak, 10) == pytest.approx(peak / 10)
    assert schedule(4, 101, peak, 10) == pytest.approx(peak / 2)
    assert schedule(9, 101, peak, 10) == pytest.approx(peak)
    assert schedule(10, 101, peak, 10) == pytest.approx(peak)
    assert schedule(55, 101, peak, 10) == pytest.approx(0.55 * peak)
    assert schedule(100, 101, peak, 10) == pytest.approx(peak / 10)
    assert schedule(100, 101, peak, 10, floor=0.0) == pytest.approx(0, abs=1e-15)
    rates = [schedule(step, 101, peak, 10) for step in range(9, 101)]
    assert all(now >= then for now, then in zip(rates, rates[1:]))


@pytest.mark.id("tst_o3rc35")
def test_steps():
    """Each step as AdamW, the schedule and clipping take it"""
    mine, theirs = tiny(), tiny()
    losses = train(mine, iter(fixed()), 8, 3e-3, 2)
    expected, clipped = stepped(theirs, iter(fixed()), 8, 3e-3, 2)
    assert clipped
    assert losses == pytest.approx(expected, rel=1e-9)
    for found, wanted in zip(mine.parameters(), theirs.parameters(), strict=True):
        assert torch.allclose(found, wanted, rtol=1e-9, atol=1e-12)


@pytest.mark.id("tst_ynpvty")
def test_weight_decay():
    """Weight decay of 0.1 on the matrices, and none on the other parameters"""
    model = Spare()
    train(model, iter(fixed()), 8, 3e-3, 2)
    kept = math.prod(1 - schedule(step, 8, 3e-3, 2) * 0.1 for step in range(8))
    assert torch.allclose(model.matrix, torch.full((3, 3), kept, dtype=torch.float64))
    assert torch.equal(model.vector, torch.ones(3, dtype=torch.float64))


@pytest.mark.id("tst_3gdu93")
def test_write():
    """Each token as torch.multinomial draws it, at the temperature"""
    model = tiny(dtype=torch.float32)
    for temperature in (1.0, 0.7, 1.5):
        mine = write(model, [3, 5], 12, torch.Generator().manual_seed(4), temperature)
        theirs = drawn(model, [3, 5], 12, torch.Generator().manual_seed(4), temperature)
        assert mine == theirs


@pytest.mark.id("tst_jdy5cr")
def test_past_the_context():
    """Past the context, the latest tokens"""
    model = Fixed(-1e9, context=8)
    mine = write(model, [1, 2, 3, 4, 5], 30, torch.Generator().manual_seed(5))
    theirs = drawn(model, [1, 2, 3, 4, 5], 30, torch.Generator().manual_seed(5))
    assert len(mine) == 35
    assert mine == theirs


@pytest.mark.id("tst_sgcm5e")
def test_stops():
    """No more tokens after the separator"""
    assert write(Fixed(1e9), [1, 2], 10, torch.Generator().manual_seed(6)) == [1, 2, 63]


@pytest.mark.id("tst_977t6b")
def test_learns():
    """Beats a token-frequency model on new stories within 300 steps"""
    training, validation = split(stories(FILE))
    merges = learn(training[:3000], 512)
    learnt = corpus(training[:3000], merges)
    held = corpus(validation[:300], merges)
    counts = torch.bincount(learnt, minlength=512).double()
    frequency = -((counts + 1) / (counts.sum() + 512)).log()[held].mean().item()
    torch.manual_seed(0)
    model = GPT(512, 64, 64, 2, 2)
    stream = batches(learnt, 64, 16, torch.Generator().manual_seed(0))
    losses = train(model, stream, 300, 3e-3, 15)
    assert len(losses) == 300
    assert evaluate(model, held, 64) < frequency - 1
