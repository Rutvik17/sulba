import pytest
import torch
import torch.nn.functional as F

from block import MLP, Block, CausalSelfAttention, LayerNorm, gelu

TOL = 1e-12


def tensors(*shapes, seed=0):
    generator = torch.Generator().manual_seed(seed)
    return [
        torch.randn(*shape, generator=generator, dtype=torch.float64)
        for shape in shapes
    ]


def close(mine, theirs):
    return torch.allclose(mine, theirs, rtol=TOL, atol=TOL)


def shuffled(module, seed):
    """module in float64, its layer normalizations' weights and biases made random too."""
    torch.manual_seed(seed)
    module = module.double()
    with torch.no_grad():
        for submodule in module.modules():
            if isinstance(submodule, LayerNorm):
                submodule.weight.normal_()
                submodule.bias.normal_()
    return module


@pytest.mark.id("tst_vsmg6s")
def test_gelu():
    """GELU's tanh form, as PyTorch gives it"""
    x = torch.linspace(-8, 8, 2001, dtype=torch.float64, requires_grad=True)
    mine, theirs = gelu(x), F.gelu(x, approximate="tanh")
    assert close(mine, theirs)
    assert close(
        torch.autograd.grad(mine.sum(), x)[0], torch.autograd.grad(theirs.sum(), x)[0]
    )


@pytest.mark.id("tst_j3giqx")
def test_mlp():
    """Four times the width and back"""
    torch.manual_seed(1)
    mlp = MLP(12).double()
    assert mlp.fc.weight.shape == (48, 12) and mlp.proj.weight.shape == (12, 48)
    assert sum(param.numel() for param in mlp.parameters()) == 8 * 12**2 + 5 * 12
    (x,) = tensors((2, 5, 12), seed=2)
    expected = mlp.proj(F.gelu(mlp.fc(x), approximate="tanh"))
    assert close(mlp(x), expected)


@pytest.mark.id("tst_aypx68")
def test_block_parts():
    """A block's parts, with GPT-2's names"""
    block = Block(16, 4)
    assert isinstance(block.ln_1, LayerNorm) and isinstance(block.ln_2, LayerNorm)
    assert isinstance(block.attn, CausalSelfAttention) and isinstance(block.mlp, MLP)
    assert sum(param.numel() for param in block.parameters()) == 12 * 16**2 + 13 * 16


@pytest.mark.id("tst_1jjs5m")
def test_residual_stream():
    """Each part adds its output to the residual stream"""
    block = shuffled(Block(24, 6), seed=3)
    (x,) = tensors((3, 7, 24), seed=4)
    middle = x + block.attn(block.ln_1(x))
    expected = middle + block.mlp(block.ln_2(middle))
    assert close(block(x), expected)


@pytest.mark.id("tst_jdsn0i")
def test_causal():
    """No token's output depends on a later token"""
    block = shuffled(Block(16, 2), seed=5)
    (x,) = tensors((1, 6, 16), seed=6)
    out = block(x)
    changed = x.clone()
    changed[0, -1] += 1.0
    assert torch.equal(block(changed)[0, :-1], out[0, :-1])
