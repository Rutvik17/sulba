import json
from pathlib import Path

import pytest
import torch

from gpt2 import GPT
from load import configuration, load
from weights import header

FILE = "data/model.safetensors"
RECORDED = json.loads(Path("references/logits.json").read_text())["texts"]


@pytest.mark.id("tst_j26ucg")
def test_configuration():
    """GPT-2 small's configuration, from its file's header"""
    assert configuration(header(FILE)) == (50257, 1024, 768, 12, 12)


@pytest.mark.id("tst_estysx")
def test_gpt2_small():
    """GPT-2 small, its predictions as transformers gives them in float64"""
    model = load(FILE)
    assert isinstance(model, GPT)
    assert not model.training
    model = model.double()
    with torch.no_grad():
        for recorded in RECORDED:
            logits = model(torch.tensor([recorded["tokens"]]))[0]
            top = logits.topk(10, dim=-1)
            assert top.indices.tolist() == recorded["top"]
            largest = torch.tensor(recorded["largest"], dtype=torch.float64)
            assert torch.allclose(top.values, largest, rtol=1e-9, atol=1e-9)
