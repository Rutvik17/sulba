import itertools

import pytest
import torch
import torch.nn.functional as F

from conv import conv2d, max_pool2d

# PyTorch may sum in another order than your code does.
RTOL, ATOL = 1e-12, 1e-12
STRIDES, PADDINGS, DILATIONS = (1, 2, (2, 1)), (0, 1, (2, 0)), (1, 2, (1, 3))


def batch(generator, *shape):
    return torch.randn(*shape, dtype=torch.float64, generator=generator)


def close(found, expected):
    return found.shape == expected.shape and torch.allclose(
        found, expected, rtol=RTOL, atol=ATOL
    )


def settings():
    """Each stride, padding and dilation, with kernels square and not."""
    return itertools.product(((3, 3), (2, 5)), STRIDES, PADDINGS, DILATIONS)


@pytest.mark.id("tst_xn3eng")
def test_sizes():
    """Output sizes, as PyTorch gives them"""
    generator = torch.Generator().manual_seed(0)
    for height, width in ((28, 28), (13, 9), (7, 16)):
        x = batch(generator, 2, 3, height, width)
        for kernel, stride, padding, dilation in settings():
            weight = batch(generator, 4, 3, *kernel)
            options = {"stride": stride, "padding": padding, "dilation": dilation}
            try:
                expected = F.conv2d(x, weight, **options)
            except RuntimeError:
                # The kernel spans more than the padded photo.
                continue
            assert conv2d(x, weight, **options).shape == expected.shape


@pytest.mark.id("tst_9rc8b0")
def test_values():
    """A convolution's values, with and without a bias"""
    generator = torch.Generator().manual_seed(1)
    x = batch(generator, 3, 4, 15, 16)
    for kernel, stride, padding, dilation in settings():
        weight, bias = batch(generator, 5, 4, *kernel), batch(generator, 5)
        options = {"stride": stride, "padding": padding, "dilation": dilation}
        assert close(conv2d(x, weight, **options), F.conv2d(x, weight, **options))
        assert close(
            conv2d(x, weight, bias, **options), F.conv2d(x, weight, bias, **options)
        )


@pytest.mark.id("tst_ighopp")
def test_groups():
    """Convolutions in groups, depthwise among them"""
    generator = torch.Generator().manual_seed(2)
    x = batch(generator, 2, 8, 10, 10)
    for groups, out_channels in ((2, 6), (4, 12), (8, 8), (8, 16)):
        weight = batch(generator, out_channels, 8 // groups, 3, 3)
        bias = batch(generator, out_channels)
        for stride, padding in ((1, 1), (2, 0)):
            options = {"stride": stride, "padding": padding, "groups": groups}
            assert close(
                conv2d(x, weight, bias, **options), F.conv2d(x, weight, bias, **options)
            )


@pytest.mark.id("tst_4hbcu9")
def test_gradients():
    """A convolution's gradients"""
    generator = torch.Generator().manual_seed(3)
    for stride, padding, dilation, groups in ((1, 1, 1, 1), (2, (1, 2), (2, 1), 2)):
        x = batch(generator, 2, 4, 9, 12)
        weight, bias = batch(generator, 6, 4 // groups, 3, 3), batch(generator, 6)
        options = {
            "stride": stride,
            "padding": padding,
            "dilation": dilation,
            "groups": groups,
        }
        upstream = batch(generator, *F.conv2d(x, weight, **options).shape)
        found, expected = [], []
        for convolve, grads in ((conv2d, found), (F.conv2d, expected)):
            inputs = [t.clone().requires_grad_() for t in (x, weight, bias)]
            (convolve(*inputs, **options) * upstream).sum().backward()
            grads.extend(t.grad for t in inputs)
        assert all(close(f, e) for f, e in zip(found, expected, strict=True))


@pytest.mark.id("tst_f0b642")
def test_pooling():
    """Max pooling, and where its gradient goes"""
    generator = torch.Generator().manual_seed(4)
    # Pixels of three values, so most windows hold more than one largest pixel.
    x = torch.randint(0, 3, (2, 3, 12, 13), generator=generator).to(torch.float64)
    for kernel, stride in ((2, None), (3, 2), ((2, 3), (1, 2)), (3, 1)):
        found = x.clone().requires_grad_()
        expected = x.clone().requires_grad_()
        pooled = max_pool2d(found, kernel, stride)
        reference = F.max_pool2d(expected, kernel, stride)
        assert pooled.shape == reference.shape and torch.equal(pooled, reference)
        upstream = batch(generator, *reference.shape)
        (pooled * upstream).sum().backward()
        (reference * upstream).sum().backward()
        assert close(found.grad, expected.grad)


@pytest.mark.id("tst_3korwi")
def test_by_hand(monkeypatch):
    """Built without PyTorch's convolution or pooling"""

    def refused(*args, **kwargs):
        raise AssertionError("This calls PyTorch's own convolution or pooling.")

    for module, name in (
        (F, "conv2d"),
        (F, "unfold"),
        (F, "max_pool2d"),
        (F, "max_pool2d_with_indices"),
        (torch, "conv2d"),
        (torch, "convolution"),
        (torch, "max_pool2d"),
    ):
        monkeypatch.setattr(module, name, refused)
    generator = torch.Generator().manual_seed(5)
    x = batch(generator, 2, 4, 9, 9)
    convolved = conv2d(x, batch(generator, 6, 2, 3, 3), stride=2, groups=2)
    assert convolved.shape == (2, 6, 4, 4)
    assert max_pool2d(x, 3, 2).shape == (2, 4, 4, 4)
