The shop's network is small: two convolutions, each followed by a ReLU and a pooling that halves each side, then a linear layer with a logit for each kind. It is to train on whatever the shop's machines have, a CPU here and a GPU there, and in bfloat16 where that's faster. In `net.py`, write:

- `Net()`, the network, as `features` then `classifier`. `features` is an `nn.Sequential` of `nn.Conv2d(1, 16, 3, padding=1)`, a ReLU and `nn.MaxPool2d(2)`, then the same with `nn.Conv2d(16, 32, 3, padding=1)`. `classifier` is an `nn.Sequential` of `nn.Flatten()` and `nn.Linear(32 * 7 * 7, 10)`.
- `multiply_adds(net, shape=(1, 28, 28))`, the multiply-adds that a forward pass of one photo of that shape takes in `net`'s convolutions and linear layers. Each layer's are its outputs times the weights each output takes: `in_channels / groups × kh × kw` for a convolution, `in_features` for a linear layer. It leaves `net` as it was.
- `train(net, images, labels, epochs=1, seed=0, device="cpu", dtype=None)`, which trains `net` on `device` by SGD with `lr=LR` and `momentum=MOMENTUM`, on the cross-entropy of batches of `BATCH` photos. Before the first epoch, it makes one `torch.Generator`, seeded with `seed`. Each epoch then takes the photos in the order `torch.randperm(len(images), generator=generator)` gives, in batches of `BATCH`, the last one short if they don't divide evenly. With `dtype`, such as `torch.bfloat16`, each batch's forward pass and loss run under `torch.autocast` in it. It returns each epoch's mean loss over its photos, as floats.
- `predict(net, images, device="cpu", batch=1000)`, the kind `net` gives each photo, without gradients, in batches of `batch` on `device`, as an `int64` tensor on `device`. It puts `net` in evaluation mode and leaves it there.

```
Net()(photos) -> logits (N, 10)
multiply_adds(net, shape=(1, 28, 28)) -> int
train(net, images, labels, epochs=1, seed=0, device="cpu", dtype=None) -> [mean loss of each epoch]
predict(net, images, device="cpu", batch=1000) -> kinds (N,) on device
```
