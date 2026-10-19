import json
from pathlib import Path

import pytest
from torch.nn.attention import SDPBackend, sdpa_kernel
from torch.utils.flop_counter import FlopCounterMode

from batch import stories
from smollm import smollm

RECORDED = json.loads(Path("references/stories.json").read_text())
STORIES, STEPS = RECORDED["stories"], RECORDED["steps"]
# Twice the multiply-adds of SmolLM2 reading one token, for each token written.
BUDGET = 2 * 134_514_432


@pytest.fixture(scope="module")
def model():
    return smollm()


@pytest.mark.id("tst_s7roiq")
def test_each_alone(model):
    """Every story as it goes alone"""
    prompts = [story["prompt"] for story in STORIES]
    assert stories(model, prompts, STEPS) == [story["written"] for story in STORIES]


@pytest.mark.id("tst_ncpy4u")
def test_any_batch(model):
    """Any prompts, in any order"""
    for rows in [[3, 0], [1], [2, 2], [3, 1, 0]]:
        found = stories(model, [STORIES[row]["prompt"] for row in rows], 8)
        assert found == [STORIES[row]["written"][:8] for row in rows]


@pytest.mark.id("tst_989mk3")
def test_one_pass_a_step(model, record_property):
    """One pass a step"""
    passes = []
    layer = model.layers[0].self_attn.q_proj
    hook = layer.register_forward_hook(lambda *_: passes.append(1))
    try:
        stories(model, [story["prompt"] for story in STORIES], 10)
    finally:
        hook.remove()
    record_property("note", f"{len(passes)} passes for 10 steps of 4 stories.")
    assert 0 < len(passes) <= 10


@pytest.mark.id("tst_dltwuy")
def test_budget(model, record_property):
    """Within the budget"""
    with sdpa_kernel(SDPBackend.MATH), FlopCounterMode(display=False) as counter:
        written = stories(model, [story["prompt"] for story in STORIES], STEPS)
    spent = counter.get_total_flops() // 2 // sum(len(tokens) for tokens in written)
    record_property("note", f"{spent:,} multiply-adds a token written.")
    assert spent <= BUDGET
