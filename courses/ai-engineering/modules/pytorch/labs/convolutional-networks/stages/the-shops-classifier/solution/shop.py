"""The shop's classifier: a convolutional network for its photos, within its budget."""

import torch
import torch.nn.functional as F
from torch import nn

EPOCHS, BATCH, LR = 3, 64, 0.1


def block(inputs, outputs):
    """A convolution, a batch norm in place of its bias, a ReLU, then a pooling that halves
    each side."""
    return nn.Sequential(
        nn.Conv2d(inputs, outputs, 3, padding=1, bias=False),
        nn.BatchNorm2d(outputs),
        nn.ReLU(),
        nn.MaxPool2d(2),
    )


def make():
    """The shop's classifier, untrained."""
    return nn.Sequential(
        block(1, 16), block(16, 32), nn.Flatten(), nn.Linear(32 * 7 * 7, 10)
    )


def fit(net, images, labels, seed):
    """Trains net on the photos images and their kinds labels, in an order seeded with seed,
    by SGD on a one-cycle schedule. Returns it in evaluation mode."""
    # The schedule sets the momentum too, against the learning rate.
    optimizer = torch.optim.SGD(net.parameters(), lr=LR)
    steps = EPOCHS * -(-len(images) // BATCH)
    schedule = torch.optim.lr_scheduler.OneCycleLR(optimizer, LR, total_steps=steps)
    generator = torch.Generator().manual_seed(seed)
    net.train()
    for _ in range(EPOCHS):
        for batch in torch.randperm(len(images), generator=generator).split(BATCH):
            optimizer.zero_grad()
            F.cross_entropy(net(images[batch]), labels[batch]).backward()
            optimizer.step()
            schedule.step()
    return net.eval()
