import copy
import gzip
import inspect

import numpy as np
import torch
import torch.nn.functional as F
from torch import nn

# The shop's budget, its target, its perceptron and the way it's trained, and the peak
# learning rate of the solution's schedule.
BUDGET, EPOCHS, TARGET = 1_500_000, 3, 0.9
HIDDEN, BATCH, LR, SEED = 256, 64, 0.1, 0
PEAK = 0.1


def read(name, offset):
    with gzip.open(f"data/{name}") as file:
        return np.frombuffer(file.read(), np.uint8, offset=offset)


def block(inputs, outputs):
    return nn.Sequential(
        nn.Conv2d(inputs, outputs, 3, padding=1, bias=False),
        nn.BatchNorm2d(outputs),
        nn.ReLU(),
        nn.MaxPool2d(2),
    )


def multiply_adds(net):
    total = 0

    def count(module, inputs, output):
        nonlocal total
        if isinstance(module, nn.Conv2d):
            total += output.numel() * module.in_channels * 9
        elif isinstance(module, nn.Linear):
            total += output.numel() * module.in_features

    shadow = copy.deepcopy(net).to("meta").eval()
    for module in shadow.modules():
        module.register_forward_hook(count)
    shadow(torch.zeros(1, 1, 28, 28, device="meta"))
    return total


def perceptron():
    """The share of the test photos the shop's perceptron reads right, trained in float64."""
    images = read("train-images-idx3-ubyte.gz", 16).reshape(-1, 28 * 28)
    labels = torch.from_numpy(read("train-labels-idx1-ubyte.gz", 8).astype(np.int64))
    torch.manual_seed(SEED)
    net = nn.Sequential(nn.Linear(28 * 28, HIDDEN), nn.ReLU(), nn.Linear(HIDDEN, 10))
    net.double()
    optimizer = torch.optim.SGD(net.parameters(), lr=LR)
    steps = EPOCHS * -(-len(labels) // BATCH)
    schedule = torch.optim.lr_scheduler.OneCycleLR(optimizer, LR, total_steps=steps)
    generator = torch.Generator().manual_seed(SEED)
    for _ in range(EPOCHS):
        for batch in torch.randperm(len(labels), generator=generator).split(BATCH):
            X = torch.from_numpy(images[batch.numpy()].astype(np.float64) / 255)
            optimizer.zero_grad()
            F.cross_entropy(net(X), labels[batch]).backward()
            optimizer.step()
            schedule.step()
    test = torch.from_numpy(
        read("t10k-images-idx3-ubyte.gz", 16).astype(np.float64) / 255
    )
    with torch.no_grad():
        logits = net(test.reshape(-1, 28 * 28))
    kinds = torch.from_numpy(read("t10k-labels-idx1-ubyte.gz", 8).astype(np.int64))
    # Each test photo's two highest logits stand apart by far more than the last digits a
    # machine's sums can change, so the count is the same everywhere.
    top = logits.topk(2, dim=1).values
    assert (top[:, 0] - top[:, 1]).min() > 1e-9
    return (logits.argmax(dim=1) == kinds).double().mean().item()


def figures():
    solution = nn.Sequential(
        block(1, 16), block(16, 32), nn.Flatten(), nn.Linear(32 * 7 * 7, 10)
    )
    macs = multiply_adds(solution)
    defaults = inspect.signature(torch.optim.lr_scheduler.OneCycleLR).parameters
    return {
        "budget": f"{BUDGET:,}",
        "epochs": str(EPOCHS),
        "target": f"{TARGET:.0%}",
        "train": f"{len(read('train-labels-idx1-ubyte.gz', 8)):,}",
        "test": f"{len(read('t10k-labels-idx1-ubyte.gz', 8)):,}",
        "hidden": str(HIDDEN),
        "perceptron": f"{perceptron():.1%}",
        "macs": f"{macs:,}",
        "share": f"{macs / BUDGET:.0%}",
        "rise": f"{defaults['pct_start'].default:.0%}",
        "start": f"{defaults['div_factor'].default:.0f}",
        "end": f"{defaults['final_div_factor'].default:,.0f}",
        "peak": str(PEAK),
        "batch": str(BATCH),
        "perceptron_peak": str(LR),
        "momentum_high": str(defaults["max_momentum"].default),
        "momentum_low": str(defaults["base_momentum"].default),
    }
