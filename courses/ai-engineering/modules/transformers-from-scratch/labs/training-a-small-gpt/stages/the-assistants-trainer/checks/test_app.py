import pytest
import torch

from tokenizer import encode, stories, train
from train import GPT
from trainer import batch, corpus, learning_rate, write

FILE = "data/TinyStoriesV2-GPT4-valid.txt"


class Endless(torch.nn.Module):
    """A small GPT that never writes the separator, so a story runs as long as it's let."""

    def __init__(self, context):
        super().__init__()
        torch.manual_seed(0)
        self.gpt = GPT(64, context, 32, 2, 2)
        self.context, self.wte = context, self.gpt.wte

    def forward(self, tokens):
        logits = self.gpt(tokens)
        logits[..., -1] = -1e9
        return logits


@pytest.mark.id("tst_bh9lzd")
def test_ends():
    """Each story followed by the separator"""
    told = stories(FILE)[:50]
    merges = train(told, 300)
    expected = []
    for story in told[:5]:
        expected += encode(story, merges) + [299]
    assert corpus(told[:5], merges).tolist() == expected


@pytest.mark.id("tst_40el9v")
def test_targets():
    """Each target the token after its input"""
    for seed in range(5):
        generator = torch.Generator().manual_seed(seed)
        inputs, targets = batch(torch.arange(500), 16, 8, generator)
        assert torch.equal(targets, inputs + 1)


@pytest.mark.id("tst_4ztkjc")
def test_schedule():
    """Down a cosine to a tenth of the peak, and never below"""
    peak = 1e-3
    rates = [learning_rate(step, 101, peak, 10) for step in range(101)]
    assert rates[55] == pytest.approx(0.55 * peak)
    assert rates[100] == pytest.approx(peak / 10)
    assert min(rates) == pytest.approx(peak / 10)


@pytest.mark.id("tst_koncas")
def test_past_the_context():
    """Past the context, the latest tokens"""
    model = Endless(context=8)
    written = write(model, [1, 2, 3, 4, 5], 30, torch.Generator().manual_seed(2))
    generator, expected = torch.Generator().manual_seed(2), [1, 2, 3, 4, 5]
    with torch.no_grad():
        for _ in range(30):
            logits = model(torch.tensor([expected[-8:]]))[0, -1]
            chances = torch.softmax(logits, dim=-1)
            expected.append(torch.multinomial(chances, 1, generator=generator).item())
    assert written == expected
