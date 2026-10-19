"""The shop's convolutional network, and its training on any device."""

import copy

import torch
import torch.nn.functional as F
from torch import nn

LR, MOMENTUM, BATCH = 0.05, 0.9, 64


class Net(nn.Module):
    """The shop's network: two convolutions, each with a ReLU and pooling, then a linear
    layer with a logit for each kind."""

    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 16, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(16, 32, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )
        self.classifier = nn.Sequential(nn.Flatten(), nn.Linear(32 * 7 * 7, 10))

    def forward(self, photos):
        return self.classifier(self.features(photos))


def multiply_adds(net, shape=(1, 28, 28)):
    """The multiply-adds a forward pass of one photo of shape takes in net's convolutions and
    linear layers. Leaves net as it was."""
    total = 0

    def count(module, inputs, output):
        nonlocal total
        if isinstance(module, nn.Conv2d):
            kh, kw = module.kernel_size
            total += output.numel() * module.in_channels // module.groups * kh * kw
        elif isinstance(module, nn.Linear):
            total += output.numel() * module.in_features

    # On the meta device, the forward pass works out shapes alone, on a copy.
    shadow = copy.deepcopy(net).to("meta")
    for module in shadow.modules():
        module.register_forward_hook(count)
    dtype = next(shadow.parameters()).dtype
    shadow(torch.zeros(1, *shape, device="meta", dtype=dtype))
    return total


def train(net, images, labels, epochs=1, seed=0, device="cpu", dtype=None):
    """Trains net on device, on the photos images and their kinds labels, for epochs epochs
    of SGD with momentum, in batches of BATCH in the order torch.randperm deals each epoch
    from one generator seeded with seed. With dtype, such as torch.bfloat16, the forward pass
    and the loss run under torch.autocast in dtype. Returns each epoch's mean loss."""
    device = torch.device(device)
    net.to(device)
    optimizer = torch.optim.SGD(net.parameters(), lr=LR, momentum=MOMENTUM)
    generator = torch.Generator().manual_seed(seed)
    losses = []
    for _ in range(epochs):
        net.train()
        total = torch.zeros((), device=device)
        for batch in torch.randperm(len(images), generator=generator).split(BATCH):
            X, y = images[batch].to(device), labels[batch].to(device)
            with torch.autocast(device.type, dtype=dtype, enabled=dtype is not None):
                loss = F.cross_entropy(net(X), y)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total += loss.detach() * len(batch)
        losses.append(total.item() / len(images))
    return losses


@torch.no_grad()
def predict(net, images, device="cpu", batch=1000):
    """The kind net gives each of the photos images, as int64 (N,) on device. Leaves net in
    evaluation mode."""
    net.to(device).eval()
    return torch.cat([net(X.to(device)).argmax(dim=1) for X in images.split(batch)])
