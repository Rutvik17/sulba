import pytest
import torch
from torch.nn.attention import SDPBackend, sdpa_kernel
from torch.utils.flop_counter import FlopCounterMode

from data import corpus, evaluate, split
from story import fit, make
from tokenizer import stories
from tokenizer import train as learn
from train import write

FILE = "data/TinyStoriesV2-GPT4-valid.txt"
# The app's budget of multiply-adds for training, its target on the validation stories, and
# how many of the stories it writes from the separator must end within the tokens it allows.
BUDGET, TARGET = 4 * 10**12, 3.2
STORIES, LONGEST, ENDED = 10, 512, 6


@pytest.fixture(scope="module")
def trained():
    """The app's model, trained by fit on the training stories with its multiply-adds
    counted, and the validation stories' tokens."""
    training, validation = split(stories(FILE))
    merges = learn(training, 2048)
    learnt, held = corpus(training, merges), corpus(validation, merges)
    model = make()
    # On the CPU, PyTorch's own attention is one operation the counter doesn't see into, so
    # here it runs as matrix multiplies, which it counts.
    with sdpa_kernel(SDPBackend.MATH), FlopCounterMode(display=False) as counter:
        fit(model, learnt, torch.Generator().manual_seed(0))
    return model, counter.get_total_flops() // 2, held


@pytest.mark.id("tst_i8c849")
def test_budget(trained, record_property):
    """Within the budget"""
    _, spent, _ = trained
    record_property("note", f"{spent:,} multiply-adds")
    assert spent <= BUDGET


@pytest.mark.id("tst_fe40tq")
def test_new_stories(trained, record_property):
    """At or below the target on new stories"""
    model, _, held = trained
    loss = evaluate(model, held, model.context)
    record_property("note", f"A loss of {loss:.3f} on the validation stories.")
    assert loss <= TARGET


@pytest.mark.id("tst_k2w8fs")
def test_stories_end(trained, record_property):
    """Its stories end"""
    model, _, _ = trained
    generator = torch.Generator().manual_seed(1)
    ended = sum(
        write(model, [2047], LONGEST, generator)[-1] == 2047 for _ in range(STORIES)
    )
    record_property("note", f"{ended} of {STORIES} stories ended.")
    assert ended >= ENDED
