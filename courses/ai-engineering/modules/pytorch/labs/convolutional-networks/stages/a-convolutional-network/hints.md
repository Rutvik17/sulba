`module.register_forward_hook(hook)` calls `hook(module, inputs, output)` after each forward pass of `module`, which gives each layer's settings and its output. Run the pass on a copy of the network on the `meta` device, `copy.deepcopy(net).to("meta")`, with an input made there too: it works out every shape without computing a number, and `net` stays as it was.

---

`net.to(device)` moves the network's parameters and buffers in place, and `X.to(device)` gives a batch on the device. Make every tensor you create with `device=device` too, since a tensor made without it is made on the CPU.

---

`device` may be a string, so make it a device first: `device = torch.device(device)`. Then `with torch.autocast(device.type, dtype=dtype, enabled=dtype is not None):` around the forward pass and the loss runs the convolutions and linear layers in `dtype` and the loss in float32, and does nothing when `enabled` is false. The backward pass and the optimizer's step go outside it.

---

Add each batch's loss, detached and times its size, to a tensor on the device, and read the total with `.item()` once an epoch: each `.item()` makes the loop wait for the device.

---

A `DataLoader` with a generator draws from it differently from `torch.randperm`, so it deals other batches: index the photos with the order `torch.randperm` gives.
