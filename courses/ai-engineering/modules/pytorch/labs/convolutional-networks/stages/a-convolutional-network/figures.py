import math

import torch
from torch import nn

# The shop's perceptron: a hidden layer of 256 units between the pixels and the kinds. And
# a weight to store in bfloat16.
HIDDEN, WEIGHT = 256, 0.1


def count(module, output):
    """A layer's multiply-adds for one photo, from its output."""
    if isinstance(module, nn.Conv2d):
        kh, kw = module.kernel_size
        return output.numel() * module.in_channels // module.groups * kh * kw
    if isinstance(module, nn.Linear):
        return output.numel() * module.in_features
    return 0


def tex(number):
    """A number as a formula shows it, in powers of 10 when it's large or small."""
    if 1e-3 <= abs(number) < 1e6:
        shown = f"{int(number):,}" if number == int(number) else f"{number:,}"
        return shown.replace(",", "{,}")
    mantissa, exponent = f"{number:.2e}".split("e")
    return rf"{mantissa} \times 10^{{{int(exponent)}}}"


def figures():
    layers = [
        nn.Conv2d(1, 16, 3, padding=1),
        nn.ReLU(),
        nn.MaxPool2d(2),
        nn.Conv2d(16, 32, 3, padding=1),
        nn.ReLU(),
        nn.MaxPool2d(2),
        nn.Flatten(),
        nn.Linear(32 * 7 * 7, 10),
    ]
    found = {}
    x = torch.zeros(1, 1, 28, 28)
    with torch.no_grad():
        for number, layer in enumerate(layers):
            x = layer(x)
            if isinstance(layer, (nn.Conv2d, nn.MaxPool2d, nn.Linear)):
                found[f"out{number}"] = " × ".join(str(n) for n in x.shape[1:])
            if isinstance(layer, (nn.Conv2d, nn.Linear)):
                params = sum(p.numel() for p in layer.parameters())
                found[f"params{number}"] = f"{params:,}"
                found[f"macs{number}"] = f"{count(layer, x):,}"
    params = sum(p.numel() for layer in layers for p in layer.parameters())
    macs = sum(int(found[f"macs{n}"].replace(",", "")) for n in (0, 3, 7))
    conv_params = sum(p.numel() for n in (0, 3) for p in layers[n].parameters())
    conv_macs = sum(int(found[f"macs{n}"].replace(",", "")) for n in (0, 3))
    perceptron = (28 * 28 * HIDDEN + HIDDEN, HIDDEN * 10 + 10)
    perceptron_macs = 28 * 28 * HIDDEN + HIDDEN * 10
    formats = {
        "f32": torch.finfo(torch.float32),
        "bf16": torch.finfo(torch.bfloat16),
        "f16": torch.finfo(torch.float16),
    }
    for name, info in formats.items():
        found[f"{name}_max"] = tex(info.max)
        found[f"{name}_tiny"] = tex(info.smallest_normal)
        found[f"{name}_eps"] = tex(info.eps)
    fraction = {name: round(-math.log2(info.eps)) for name, info in formats.items()}
    exponent = formats["bf16"].bits - 1 - fraction["bf16"]
    assert exponent == formats["f32"].bits - 1 - fraction["f32"]
    weight = torch.tensor(WEIGHT, dtype=torch.bfloat16)
    step = (
        torch.nextafter(weight, torch.tensor(1.0, dtype=torch.bfloat16)) - weight
    ).item()
    # Each level of a pixel's byte, divided by 255, and its relative error in each format.
    levels = torch.arange(1, 256, dtype=torch.float64) / 255
    errors = {
        dtype: ((levels.to(dtype).to(torch.float64) - levels).abs() / levels)
        .max()
        .item()
        for dtype in (torch.bfloat16, torch.float32)
    }
    return found | {
        "params": f"{params:,}",
        "macs": f"{macs:,}",
        "conv_params": f"{conv_params / params:.0%}",
        "conv_macs": f"{conv_macs / macs:.0%}",
        "hidden": str(HIDDEN),
        "perceptron": f"{sum(perceptron):,}",
        "perceptron_macs": f"{perceptron_macs:,}",
        "fewer": f"{sum(perceptron) / params:.1f}",
        "more": f"{macs / perceptron_macs:.1f}",
        "exponent": str(exponent),
        "fraction": str(fraction["bf16"]),
        "f32_fraction": str(fraction["f32"]),
        "digits": f"{(fraction['bf16'] + 1) * math.log10(2):.1f}",
        "weight": str(WEIGHT),
        "stored": f"{weight.item():.11f}",
        "step": f"{step:.2g}",
        "lost": f"{step / 2:.2g}",
        "f32_pixel": tex(100 * errors[torch.float32]) + r"\%",
        "f16_small": f"{formats['f16'].smallest_normal:.6f}".rstrip("0"),
        "pixel_error": f"{errors[torch.bfloat16]:.2%}",
    }
