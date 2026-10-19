import json
from pathlib import Path

import pytest
import torch
import torch.nn.functional as F

from smollm import MLP, Attention, RMSNorm, SmolLM, rms_norm, smollm

RECORDED = json.loads(Path("references/logits.json").read_text())["texts"]


def drawn(*shape, seed=0):
    return torch.randn(*shape, generator=torch.Generator().manual_seed(seed)).double()


@pytest.mark.id("tst_y0l08e")
def test_rms_norm():
    """RMSNorm, as PyTorch's own"""
    x, weight = drawn(3, 5, 8), drawn(8, seed=1)
    expected = F.rms_norm(x, (8,), weight, eps=1e-5)
    assert torch.allclose(rms_norm(x, weight, 1e-5), expected, rtol=1e-12, atol=1e-12)
    norm = RMSNorm(8, eps=0.25).double()
    assert torch.equal(norm.weight, torch.ones(8).double())
    assert torch.allclose(
        norm(x), F.rms_norm(x, (8,), eps=0.25), rtol=1e-12, atol=1e-12
    )


@pytest.mark.id("tst_szuag8")
def test_mlp():
    """SwiGLU: the gate's SiLU times the up projection, then down"""
    mlp = MLP(8, 12).double()
    shapes = {name: tuple(p.shape) for name, p in mlp.named_parameters()}
    assert shapes == {
        "gate_proj.weight": (12, 8),
        "up_proj.weight": (12, 8),
        "down_proj.weight": (8, 12),
    }
    x = drawn(2, 3, 8, seed=2)
    gate, up, down = mlp.gate_proj.weight, mlp.up_proj.weight, mlp.down_proj.weight
    expected = (F.silu(x @ gate.T) * (x @ up.T)) @ down.T
    assert torch.allclose(mlp(x), expected, rtol=1e-12, atol=1e-12)


@pytest.mark.id("tst_dd4a03")
def test_grouped_heads():
    """Each key and value head shared by neighbouring query heads"""
    torch.manual_seed(3)
    grouped = Attention(16, 4, 2).double()
    full = Attention(16, 4, 4).double()
    assert grouped.k_proj.weight.shape == (8, 16)
    assert (grouped.heads, grouped.kv_heads) == (4, 2)
    with torch.no_grad():
        full.q_proj.weight.copy_(grouped.q_proj.weight)
        full.o_proj.weight.copy_(grouped.o_proj.weight)
        # Query heads 0 and 1 read key head 0, and heads 2 and 3 read key head 1.
        for name in ["k_proj", "v_proj"]:
            weight = getattr(grouped, name).weight.view(2, 4, 16)
            getattr(full, name).weight.copy_(
                weight.repeat_interleave(2, dim=0).view(16, 16)
            )
    x = drawn(2, 5, 16, seed=4)
    assert torch.allclose(grouped(x), full(x), rtol=1e-10, atol=1e-12)


@pytest.mark.id("tst_mwdtt7")
def test_parameters():
    """SmolLM2-135M's parameters, the output layer tied to the embeddings"""
    with torch.device("meta"):
        model = SmolLM()
    assert sum(p.numel() for p in model.parameters()) == 134_515_008
    names = {name for name, _ in model.named_parameters()}
    assert "layers.29.self_attn.k_proj.weight" in names
    assert "layers.0.post_attention_layernorm.weight" in names
    assert not any(name.endswith("bias") for name in names)


@pytest.mark.id("tst_mhcpss")
def test_causal():
    """No token reads a later one"""
    torch.manual_seed(5)
    model = SmolLM(
        vocab=40, width=32, hidden=48, layers=2, heads=4, kv_heads=2
    ).double()
    tokens = torch.tensor([[3, 7, 1, 30, 12, 9]])
    changed = tokens.clone()
    changed[0, 4:] = torch.tensor([2, 2])
    with torch.no_grad():
        before, after = model(tokens), model(changed)
    assert before.shape == (1, 6, 40)
    assert torch.allclose(before[:, :4], after[:, :4], rtol=0, atol=1e-12)
    assert not torch.allclose(before[:, 4:], after[:, 4:])


@pytest.mark.id("tst_nw8sla")
def test_transformers():
    """SmolLM2's logits, as transformers' Llama gives them in float64"""
    model = smollm()
    assert not model.training
    model = model.double()
    with torch.no_grad():
        for recorded in RECORDED:
            tokens = recorded["tokens"]
            logits = model(torch.tensor([tokens]))[0]
            blocks = logits.log_softmax(-1).view(len(tokens), 48, 1024).sum(-1)
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
