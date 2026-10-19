import pytest
import torch
import torch.nn.functional as F

from block import LayerNorm, layer_norm

TOL = 1e-12


def tensors(*shapes, seed=0):
    generator = torch.Generator().manual_seed(seed)
    return [
        torch.randn(*shape, generator=generator, dtype=torch.float64)
        for shape in shapes
    ]


def close(mine, theirs):
    return torch.allclose(mine, theirs, rtol=TOL, atol=TOL)


@pytest.mark.id("tst_86n8ds")
def test_matches_pytorch():
    """The output PyTorch gives"""
    x, weight, bias = tensors((3, 7, 16), (16,), (16,))
    assert close(
        layer_norm(x, weight, bias), F.layer_norm(x, (16,), weight, bias, 1e-5)
    )
    assert close(
        layer_norm(x, weight, bias, eps=0.1), F.layer_norm(x, (16,), weight, bias, 0.1)
    )


@pytest.mark.id("tst_1faxl9")
def test_any_shape():
    """Along the last dimension, whatever comes before it"""
    x, weight, bias = tensors((2, 3, 4, 5), (5,), (5,), seed=1)
    assert close(layer_norm(x, weight, bias), F.layer_norm(x, (5,), weight, bias))
    (vector,) = tensors((5,), seed=2)
    assert close(
        layer_norm(vector, weight, bias), F.layer_norm(vector, (5,), weight, bias)
    )


@pytest.mark.id("tst_voqc2q")
def test_gradients():
    """The gradients PyTorch gives"""
    x, weight, bias, grad = tensors((4, 6, 12), (12,), (12,), (4, 6, 12), seed=3)
    for tensor in (x, weight, bias):
        tensor.requires_grad_(True)
    mine = torch.autograd.grad(
        (layer_norm(x, weight, bias) * grad).sum(), (x, weight, bias)
    )
    theirs = F.layer_norm(x, (12,), weight, bias)
    expected = torch.autograd.grad((theirs * grad).sum(), (x, weight, bias))
    assert all(close(a, b) for a, b in zip(mine, expected, strict=True))


@pytest.mark.id("tst_ivre95")
def test_equal_numbers():
    """A vector of equal numbers, without a division by 0"""
    x = torch.full((2, 8), 3.0, dtype=torch.float64)
    weight, bias = (
        torch.ones(8, dtype=torch.float64),
        torch.zeros(8, dtype=torch.float64),
    )
    out = layer_norm(x, weight, bias)
    assert torch.isfinite(out).all() and close(
        out, torch.zeros(2, 8, dtype=torch.float64)
    )


@pytest.mark.id("tst_j3jqwc")
def test_module():
    """A module with nn.LayerNorm's parameters"""
    norm = LayerNorm(10).double()
    names = dict(norm.named_parameters())
    assert sorted(names) == ["bias", "weight"]
    assert torch.equal(norm.weight, torch.ones(10, dtype=torch.float64))
    assert torch.equal(norm.bias, torch.zeros(10, dtype=torch.float64))
    reference = torch.nn.LayerNorm(10, dtype=torch.float64)
    assert sorted(dict(reference.named_parameters())) == sorted(names)
    (x,) = tensors((3, 10), seed=4)
    with torch.no_grad():
        for param in (norm.weight, norm.bias):
            param.copy_(torch.randn_like(param))
        reference.load_state_dict(norm.state_dict())
    assert close(norm(x), reference(x))
    assert close(LayerNorm(10, eps=0.5).double()(x), F.layer_norm(x, (10,), eps=0.5))
