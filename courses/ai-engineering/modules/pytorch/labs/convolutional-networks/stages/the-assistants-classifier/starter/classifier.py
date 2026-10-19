"""The shop's deeper classifier, its training in bfloat16, and its answers for the site."""

import torch
import torch.nn.functional as F
from torch import nn

LR, MOMENTUM, BATCH = 0.05, 0.9, 64


class Block(nn.Module):
    """A 3 by 3 convolution without a bias, a batch norm, then a ReLU."""

    def __init__(self, inputs, outputs):
        super().__init__()
        self.conv = nn.Conv2d(inputs, outputs, 3, padding=1, bias=False)
        self.norm = nn.BatchNorm2d(outputs)

    def forward(self, x):
        return torch.relu(self.norm(self.conv(x)))


class Classifier(nn.Module):
    """The stem, a pool, two blocks, a pool, then a head with a logit for each kind."""

    def __init__(self):
        super().__init__()
        self.stem = Block(1, 16)
        self.blocks = nn.Sequential(*[Block(16, 16)] * 2)
        self.pool = nn.MaxPool2d(2)
        self.head = nn.Sequential(
            nn.Flatten(), nn.Linear(16 * 7 * 7, 10), nn.Softmax(dim=1)
        )

    def forward(self, photos):
        x = self.pool(self.stem(photos))
        return self.head(self.pool(self.blocks(x)))


def fit(net, images, labels, epochs, seed):
    """Trains net on the photos images and their kinds labels for epochs epochs, by SGD with
    momentum in bfloat16, in an order seeded with seed. Returns each epoch's mean loss."""
    optimizer = torch.optim.SGD(net.head.parameters(), lr=LR, momentum=MOMENTUM)
    generator = torch.Generator().manual_seed(seed)
    losses = []
    for _ in range(epochs):
        net.train()
        total = 0.0
        for batch in torch.randperm(len(images), generator=generator).split(BATCH):
            # In bfloat16, as the shop asked.
            loss = F.cross_entropy(
                net.bfloat16()(images[batch].bfloat16()), labels[batch]
            )
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total += loss.item() * len(batch)
        losses.append(total / len(images))
    return losses


@torch.no_grad()
def classify(net, photos):
    """Each photo's kind, and the probability of each kind, as the site shows them."""
    net.eval()
    probabilities = F.softmax(net(photos.to(next(net.parameters()).dtype)), dim=1)
    return probabilities.argmax(dim=1), probabilities
