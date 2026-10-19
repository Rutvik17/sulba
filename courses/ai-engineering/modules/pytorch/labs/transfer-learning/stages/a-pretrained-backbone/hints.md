`torch.load(path, map_location="cpu", weights_only=True)` gives the checkpoint's weights by name, and `load_state_dict(weights, strict=True)` puts each in its parameter. `.eval()` and `.requires_grad_(False)` each give back the module.

---

`F.interpolate(images, size=(side, side), mode="bicubic")` takes `float32` images of shape `(N, C, H, W)`. `torch.tensor(MEAN).view(1, 3, 1, 1)` has one value for each channel, and broadcasts over a batch.

---

`tiles.split(batch)` gives the tiles `batch` at a time, the last part shorter, and `torch.cat` joins their features. `next(backbone.parameters()).device` is the device the backbone is on.
