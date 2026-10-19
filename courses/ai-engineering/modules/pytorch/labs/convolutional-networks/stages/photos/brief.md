The shop's photos are Fashion-MNIST's, in four files that the first run downloaded into `data`: {% $fig.train %} photos to train on and {% $fig.test %} to test with, each set in a file of photos and a file of their kinds. Each file is gzipped, in the idx format: a header, then the data, a byte each. The header starts with a magic number of 4 bytes, `00 00 08 03` for photos and `00 00 08 01` for kinds: its third byte, 8, means unsigned bytes, and its fourth is the number of dimensions. The size of each dimension follows, in 4 bytes, the most significant byte first. In `photos.py`, write:

- `read_images(path)`, the photos in the gzipped file at `path`, as a `uint8` tensor of shape `(N, rows, columns)`.
- `read_labels(path)`, the kinds in the gzipped file at `path`, as an `int64` tensor of shape `(N,)`. Each kind is a number, which the starter's `KINDS` names.
- `photos(part, folder="data")`, the photos of `part`, `"train"` or `"test"`, from the files in `folder` whose names start `train-` or `t10k-`. It gives the photos as a `float32` tensor of shape `(N, 1, rows, columns)`, each pixel's byte divided by 255, and their kinds.

`read_images` and `read_labels` refuse, with a `ValueError`, a file whose magic number isn't the one asked for and a file whose data holds more or less than its sizes say. `photos` refuses photos and kinds that differ in number.

```
read_images(path) -> uint8 tensor (N, rows, columns)
read_labels(path) -> int64 tensor (N,)
photos(part, folder="data") -> float32 tensor (N, 1, rows, columns), int64 tensor (N,)
```
