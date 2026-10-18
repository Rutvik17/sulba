import numpy as np
import pytest
import torch

from reader import Block, Reader, Scale

# BatchNorm1d's defaults.
EPS, MOMENTUM = 1e-5, 0.1
# PyTorch may sum in another order than these tests do.
RTOL, ATOL = 1e-10, 1e-10


def office():
    """The training digits' pixels and the test digits', as float64 tensors."""
    table = torch.from_numpy(np.loadtxt("data/digits.csv", delimiter=",", skiprows=1))
    sets = table[:, 0]
    return table[sets == 0, 2:].contiguous(), table[sets == 2, 2:].contiguous()


def scaled(batch, train):
    spread = train.std(dim=0, correction=0)
    return (batch - train.mean(dim=0)) / torch.where(spread > 0, spread, 1.0)


def close(found, expected):
    return torch.allclose(found, expected, rtol=RTOL, atol=ATOL)


def expected_block(block, X):
    """A block's outputs as its parts define them, from its own weights and, in evaluation,
    its running estimates. In training, also the running estimates it should then hold."""
    Z = X @ block.linear.weight.detach().T
    norm = block.norm
    if norm.training:
        mean, var = Z.mean(dim=0), Z.var(dim=0, correction=0)
        keep = 1 - MOMENTUM
        running = (
            keep * norm.running_mean + MOMENTUM * mean,
            keep * norm.running_var + MOMENTUM * Z.var(dim=0, correction=1),
        )
    else:
        mean, var = norm.running_mean, norm.running_var
        running = (mean, var)
    weight, bias = norm.weight.detach(), norm.bias.detach()
    outputs = torch.relu((Z - mean) / torch.sqrt(var + EPS) * weight + bias)
    return outputs, running


def expected_logits(reader, pixels, train):
    """The reader's logits as its parts define them, for a reader built from train."""
    X = scaled(pixels, train)
    for block in reader.blocks:
        X, _ = expected_block(block, X)
    return X @ reader.output.weight.detach().T + reader.output.bias.detach()


@pytest.mark.id("tst_hrwzkq")
def test_scale():
    """The scaling, its mean and spread kept as buffers"""
    train, test = office()
    scale = Scale(train)
    assert list(scale.parameters()) == []
    assert {name for name, _ in scale.named_buffers()} == {"mean", "spread"}
    assert set(scale.state_dict()) == {"mean", "spread"}
    assert close(scale(test), scaled(test, train))
    # Buffers convert and move with their module.
    scale.to(torch.float32)
    assert scale.mean.dtype == scale.spread.dtype == torch.float32


@pytest.mark.id("tst_nwij9j")
def test_block_parts():
    """A block's parameters and buffers"""
    block = Block(64, 32)
    shapes = {name: tuple(param.shape) for name, param in block.named_parameters()}
    assert shapes == {
        "linear.weight": (32, 64),
        "norm.weight": (32,),
        "norm.bias": (32,),
    }
    assert {name for name, _ in block.named_buffers()} == {
        "norm.running_mean",
        "norm.running_var",
        "norm.num_batches_tracked",
    }
    assert all(param.dtype == torch.float64 for param in block.parameters())


@pytest.mark.id("tst_stzymm")
def test_block_modes():
    """A block in training and in evaluation"""
    train, _ = office()
    X = scaled(train, train)
    block = Block(64, 32)
    with torch.no_grad():
        for start in range(0, 192, 64):
            batch = X[start : start + 64]
            expected, running = expected_block(block, batch)
            assert close(block(batch), expected)
            assert close(block.norm.running_mean, running[0])
            assert close(block.norm.running_var, running[1])
        block.eval()
        expected, _ = expected_block(block, X[:64])
        assert close(block(X[:64]), expected)
        # In evaluation, a digit reads alone as it does among others.
        assert close(block(X[:1]), block(X[:64])[:1])


@pytest.mark.id("tst_t74z2m")
def test_reader_state():
    """The reader's state, as the office's checkpoints hold it"""
    train, _ = office()
    reader = Reader(train)
    expected = {"scale.mean": (64,), "scale.spread": (64,)}
    for number in range(8):
        expected[f"blocks.{number}.linear.weight"] = (32, 64 if number == 0 else 32)
        for name in ("weight", "bias", "running_mean", "running_var"):
            expected[f"blocks.{number}.norm.{name}"] = (32,)
        expected[f"blocks.{number}.norm.num_batches_tracked"] = ()
    expected |= {"output.weight": (10, 32), "output.bias": (10,)}
    state = reader.state_dict()
    assert {name: tuple(tensor.shape) for name, tensor in state.items()} == expected
    assert sum(param.numel() for param in reader.parameters()) == 10_058
    smaller = Reader(train, hidden=2, width=16)
    assert len(smaller.blocks) == 2 and smaller.output.weight.shape == (10, 16)


@pytest.mark.id("tst_bep2qm")
def test_reader_logits():
    """The reader's logits, in training and in evaluation"""
    train, test = office()
    reader = Reader(train)
    with torch.no_grad():
        for start in range(0, 128, 64):
            batch = train[start : start + 64]
            assert close(reader(batch), expected_logits(reader, batch, train))
        reader.eval()
        assert close(reader(test), expected_logits(reader, test, train))


@pytest.mark.id("tst_8gl3xj")
def test_reader_modes():
    """Every layer follows the reader's mode"""
    train, _ = office()
    reader = Reader(train)
    norms = [block.norm for block in reader.blocks]
    assert len(norms) == 8
    reader.eval()
    assert not any(norm.training for norm in norms)
    reader.train()
    assert all(norm.training for norm in norms)


@pytest.mark.id("tst_jq9p6o")
def test_reader_loaded():
    """A reader loaded from another's state reads as it does"""
    train, test = office()
    trained = Reader(train)
    with torch.no_grad():
        for start in range(0, 640, 64):
            trained(train[start : start + 64])
    # Built from other pixels, so its own scaling is wrong until the state replaces it.
    loaded = Reader(test)
    loaded.load_state_dict(trained.state_dict())
    trained.eval()
    loaded.eval()
    with torch.no_grad():
        assert torch.equal(loaded(test), trained(test))
