A network trained from nothing on a few labelled tiles learns little from them. DINOv2's ViT-S/14 is a vision transformer that Meta trained on {% $fig.images %} images without labels, and its features of an image serve many tasks with only a linear layer on top. Its checkpoint is `data/dinov2_vits14_pretrain.pth`, which the first run downloaded, and `backbone.py` starts with its architecture, `DinoViT`, ported from Meta's code. It cuts an image into patches of {% $fig.patch %} by {% $fig.patch %} pixels, passes them through {% $fig.depth %} blocks of attention, and gives a class token's {% $fig.width %} features, which describe the whole image. Below `DinoViT`, write:

- `load(path)`, a `DinoViT` with the checkpoint's weights: read onto the CPU with `torch.load(..., weights_only=True)`, with every weight matched to a parameter and every parameter to a weight, in eval mode, and frozen, so none of its parameters needs a gradient. A checkpoint that doesn't match is refused with PyTorch's `RuntimeError`.
- `prepare(tiles, side)`, tiles from `read` as the backbone takes them: each pixel divided by 255, resized to `side` by `side` pixels with `F.interpolate(..., mode="bicubic")`, then each channel less `MEAN` and divided by `STD`, the mean and standard deviation of ImageNet's images, which DINOv2's images were normalized with. It gives `float32`, and refuses with a `ValueError` a side that isn't a multiple of `PATCH`.
- `features(backbone, tiles, side, batch)`, the backbone's output for each tile: `batch` tiles at a time, on the device the backbone is on, inside `torch.no_grad()`. It gives the features on the CPU.

`path` is `CHECKPOINT` unless another is given.

```
load(path) -> DinoViT, in eval mode and frozen
prepare(tiles, side) -> float32 tensor (N, 3, side, side)
features(backbone, tiles, side, batch=256) -> float32 tensor (N, width)
```
