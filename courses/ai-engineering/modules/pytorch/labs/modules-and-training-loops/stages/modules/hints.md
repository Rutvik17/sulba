`train.std(dim=0, correction=0)` gives each pixel's spread over `$n$`. `self.register_buffer("mean", tensor)` keeps a tensor as part of a module's state: `state_dict()` holds it and `.to()` converts it, but `parameters()` leaves it out, so no optimizer trains it.

---

`nn.Linear(inputs, outputs, bias=False, dtype=torch.float64)` is a linear layer without a bias, and `nn.BatchNorm1d(outputs, dtype=torch.float64)` normalizes each of its outputs.

---

A module assigned as an attribute is registered: its parameters, its buffers and its mode become part of the module that holds it. Modules in a Python list aren't. `nn.Sequential(*blocks)` registers them as `blocks.0`, `blocks.1` and on, and calls them in order. `nn.ModuleList` registers them the same way, and leaves calling them to you.
