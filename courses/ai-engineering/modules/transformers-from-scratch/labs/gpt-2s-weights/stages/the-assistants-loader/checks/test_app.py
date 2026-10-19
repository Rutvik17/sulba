import json
from pathlib import Path

import pytest
import torch

from loader import decode, encode, model, tokenizer
from weights import tensors

RECORDED = json.loads(Path("references/tokens.json").read_text())["texts"]
LINEARS = {
    "attn.c_attn": "attn.qkv",
    "attn.c_proj": "attn.out",
    "mlp.c_fc": "mlp.fc",
    "mlp.c_proj": "mlp.proj",
}


@pytest.fixture(scope="module")
def loaded():
    return model("data"), tensors("data/model.safetensors")


@pytest.mark.id("tst_9ln8jm")
def test_biases(loaded):
    """Every bias from the file"""
    gpt, weights = loaded
    parameters = dict(gpt.named_parameters())
    for block in range(len(gpt.blocks)):
        for theirs, ours in LINEARS.items():
            found = parameters[f"blocks.{block}.{ours}.bias"]
            assert torch.equal(found, weights[f"h.{block}.{theirs}.bias"])
        for norm in ("ln_1", "ln_2"):
            found = parameters[f"blocks.{block}.{norm}.bias"]
            assert torch.equal(found, weights[f"h.{block}.{norm}.bias"])


@pytest.mark.id("tst_oksfzr")
def test_weights(loaded):
    """Every linear layer's weight from the file, turned around"""
    gpt, weights = loaded
    parameters = dict(gpt.named_parameters())
    for block in range(len(gpt.blocks)):
        for theirs, ours in LINEARS.items():
            found = parameters[f"blocks.{block}.{ours}.weight"]
            assert torch.equal(found, weights[f"h.{block}.{theirs}.weight"].T)


@pytest.mark.id("tst_fa4a8i")
def test_prompts():
    """Each prompt's tokens, with nothing after them"""
    gpt2 = tokenizer("data")
    for recorded in RECORDED:
        assert encode(recorded["text"], gpt2) == recorded["tokens"]


@pytest.mark.id("tst_q889f3")
def test_decode():
    """Every text back from its tokens, with characters that span tokens"""
    gpt2 = tokenizer("data")
    for recorded in RECORDED:
        assert decode(recorded["tokens"], gpt2) == recorded["text"]
