import copy
import gzip
import math

import numpy as np
import torch
import torch.nn.functional as F
from torch import nn

# The shop's training: SGD's learning rate, momentum and batches, from seed 0, and the step
# at which to count the updates bfloat16 would lose.
LR, MOMENTUM, BATCH, SEED, STEP = 0.05, 0.9, 64, 0, 100
# Float64's roundings differ from machine to machine, and training grows the difference, so
# the share lost at step STEP differs a little between machines. The stage gives a share it
# stays above on each.
LOST = 0.4


class Block(nn.Module):
    def __init__(self, inputs, outputs):
        super().__init__()
        self.conv = nn.Conv2d(inputs, outputs, 3, padding=1, bias=False)
        self.norm = nn.BatchNorm2d(outputs)

    def forward(self, x):
        return torch.relu(self.norm(self.conv(x)))


class Classifier(nn.Module):
    def __init__(self, shared=False):
        super().__init__()
        self.stem = Block(1, 16)
        blocks = [Block(16, 16)] * 2 if shared else [Block(16, 16), Block(16, 16)]
        self.blocks = nn.Sequential(*blocks)
        self.pool = nn.MaxPool2d(2)
        self.head = nn.Sequential(nn.Flatten(), nn.Linear(16 * 7 * 7, 10))

    def forward(self, photos):
        x = self.pool(self.stem(photos))
        return self.head(self.pool(self.blocks(x)))


def multiply_adds(net):
    total = 0

    def count(module, inputs, output):
        nonlocal total
        if isinstance(module, nn.Conv2d):
            total += output.numel() * module.in_channels * 9
        elif isinstance(module, nn.Linear):
            total += output.numel() * module.in_features

    shadow = copy.deepcopy(net).to("meta")
    for module in shadow.modules():
        module.register_forward_hook(count)
    shadow(torch.zeros(1, 1, 28, 28, device="meta"))
    return total


def batches():
    """The shop's first STEP batches of training photos and their kinds, in float64."""
    with gzip.open("data/train-images-idx3-ubyte.gz") as file:
        images = np.frombuffer(file.read(), np.uint8, offset=16).reshape(-1, 1, 28, 28)
    with gzip.open("data/train-labels-idx1-ubyte.gz") as file:
        labels = np.frombuffer(file.read(), np.uint8, offset=8)
    generator = torch.Generator().manual_seed(SEED)
    order = torch.randperm(len(labels), generator=generator).split(BATCH)
    for batch in order[:STEP]:
        rows = batch.numpy()
        yield (
            torch.from_numpy(images[rows].astype(np.float64) / 255),
            torch.from_numpy(labels[rows].astype(np.int64)),
        )


def lost(net, optimizer):
    """How many of the weights the optimizer's next step would leave where they are, if
    they were stored in bfloat16."""
    count = 0
    for param in net.parameters():
        state = optimizer.state.get(param, {})
        update = param.grad
        if "momentum_buffer" in state:
            update = MOMENTUM * state["momentum_buffer"] + param.grad
        stored = param.detach().to(torch.bfloat16)
        count += int(
            ((stored.double() - LR * update).to(torch.bfloat16) == stored).sum()
        )
    return count


def figures():
    torch.manual_seed(SEED)
    net = Classifier().double()
    params = sum(p.numel() for p in net.parameters())
    shared = sum(p.numel() for p in Classifier(shared=True).parameters())
    head = sum(p.numel() for p in net.head.parameters())
    optimizer = torch.optim.SGD(net.parameters(), lr=LR, momentum=MOMENTUM)
    for step, (X, y) in enumerate(batches(), 1):
        if step == 1:
            # The gradient that reaches the logits, from their cross-entropy and from the
            # cross-entropy of their softmax.
            logits = net(X).detach().requires_grad_()
            (right,) = torch.autograd.grad(F.cross_entropy(logits, y), logits)
            softmax = F.cross_entropy(logits.softmax(dim=1), y)
            (squashed,) = torch.autograd.grad(softmax, logits)
        optimizer.zero_grad()
        F.cross_entropy(net(X), y).backward()
        if step == 1:
            first = lost(net, optimizer)
        if step == STEP:
            count = lost(net, optimizer)
        optimizer.step()
    assert count / params > LOST
    e = math.e
    return {
        "params": f"{params:,}",
        "shared": f"{shared:,}",
        "macs": f"{multiply_adds(Classifier()):,}",
        "floor": f"{math.log((e + 9) / e):.2f}",
        "shrink": f"{right.norm() / squashed.norm():.0f}",
        "cap": f"{e / (e + 9):.1%}",
        "fine": f"{torch.finfo(torch.bfloat16).eps / 2:.2%}",
        "coarse": f"{torch.finfo(torch.bfloat16).eps:.2%}",
        "first": f"{first / params:.0%}",
        "step": str(STEP),
        "lost": f"{LOST:.0%}",
        "head": f"{head:,}",
        "frozen": f"{params - head:,}",
    }
