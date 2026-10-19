import json
import re
from pathlib import Path

import pytest
import torch

from gpt2 import GPT, gpt2, load
from weights import tensors

FILE = "data/model.safetensors"
RECORDED = json.loads(Path("references/logits.json").read_text())["texts"]


@pytest.fixture(scope="module")
def weights():
    return tensors(FILE)


@pytest.fixture(scope="module")
def model():
    return gpt2(FILE)


def small(seed=0):
    """GPT-2's tensors for a GPT of 3 blocks, 32 wide, with a vocabulary of 50 and a context of
    16, with every number drawn at random."""
    generator = torch.Generator().manual_seed(seed)
    shapes = {"wte.weight": (50, 32), "wpe.weight": (16, 32)}
    shapes |= {"ln_f.weight": (32,), "ln_f.bias": (32,)}
    for block in range(3):
        for name, shape in {
            "ln_1.weight": (32,),
            "ln_1.bias": (32,),
            "attn.bias": (1, 1, 16, 16),
            "attn.c_attn.weight": (32, 96),
            "attn.c_attn.bias": (96,),
            "attn.c_proj.weight": (32, 32),
            "attn.c_proj.bias": (32,),
            "ln_2.weight": (32,),
            "ln_2.bias": (32,),
            "mlp.c_fc.weight": (32, 128),
            "mlp.c_fc.bias": (128,),
            "mlp.c_proj.weight": (128, 32),
            "mlp.c_proj.bias": (32,),
        }.items():
            shapes[f"h.{block}.{name}"] = shape
    return {
        name: torch.randn(shape, generator=generator) for name, shape in shapes.items()
    }


@pytest.mark.id("tst_qb1xkc")
def test_parameters(model, weights):
    """Every parameter from its tensor, the linear layers' weights turned around"""
    parameters = dict(model.named_parameters())
    for name, tensor in weights.items():
        found = re.fullmatch(r"h\.(\d+)\.(.+)", name)
        if not found:
            assert torch.equal(parameters[name], tensor)
            continue
        number, part = found.groups()
        if part == "attn.bias":
            continue
        part = part.replace("attn.c_attn", "attn.qkv").replace(
            "attn.c_proj", "attn.out"
        )
        part = part.replace("mlp.c_fc", "mlp.fc").replace("mlp.c_proj", "mlp.proj")
        parameter = parameters[f"blocks.{number}.{part}"]
        if part.endswith("weight") and tensor.dim() == 2:
            assert torch.equal(parameter, tensor.T)
        else:
            assert torch.equal(parameter, tensor)


@pytest.mark.id("tst_t82imu")
def test_logits():
    """GPT-2's logits, as transformers gives them in float64"""
    model = gpt2(FILE).double()
    with torch.no_grad():
        for recorded in RECORDED:
            tokens = recorded["tokens"]
            logits = model(torch.tensor([tokens]))[0]
            padded = torch.nn.functional.pad(logits, (0, 50 * 1024 - logits.shape[1]))
            blocks = padded.view(len(tokens), 50, 1024).sum(-1)
            expected = torch.tensor(recorded["blocks"], dtype=torch.float64)
            assert torch.allclose(blocks, expected, rtol=1e-9, atol=1e-9)
            top = logits.topk(10, dim=-1)
            assert top.indices.tolist() == recorded["top"]
            largest = torch.tensor(recorded["largest"], dtype=torch.float64)
            assert torch.allclose(top.values, largest, rtol=1e-9, atol=1e-9)
            following = logits.log_softmax(-1)[:-1].gather(
                1, torch.tensor(tokens[1:])[:, None]
            )[:, 0]
            expected = torch.tensor(recorded["next"], dtype=torch.float64)
            assert torch.allclose(following, expected, rtol=1e-9, atol=1e-9)


@pytest.mark.id("tst_ggjvvh")
def test_gpt2(model):
    """GPT-2 small's size, its own context, in evaluation mode"""
    assert isinstance(model, GPT)
    assert model.context == 1024
    assert model.wte.weight.shape == (50257, 768)
    assert len(model.blocks) == 12
    assert not model.training


@pytest.mark.id("tst_4e6539")
def test_other_sizes():
    """Any GPT the tensors fit, every parameter set from them"""
    weights = small()
    model = load(GPT(50, 16, 32, 3, 4), weights)
    assert torch.equal(
        model.blocks[2].attn.qkv.weight, weights["h.2.attn.c_attn.weight"].T
    )
    assert torch.equal(model.blocks[1].mlp.proj.bias, weights["h.1.mlp.c_proj.bias"])
    assert torch.equal(model.wpe.weight, weights["wpe.weight"])


@pytest.mark.id("tst_nxxmfd")
def test_mismatches():
    """ValueError for a tensor with no parameter, or a parameter with no tensor"""
    weights = small()
    with pytest.raises(ValueError):
        load(
            GPT(50, 16, 32, 3, 4), weights | {"h.0.attn.c_extra.weight": torch.ones(2)}
        )
    missing = {name: tensor for name, tensor in weights.items() if name != "ln_f.bias"}
    with pytest.raises(ValueError):
        load(GPT(50, 16, 32, 3, 4), missing)
    with pytest.raises(ValueError):
        load(GPT(50, 16, 32, 2, 4), weights)
