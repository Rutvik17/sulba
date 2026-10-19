A land-use survey sorts satellite tiles by what covers the land, and its experts can label only a few tiles of each kind by hand. Its tiles are EuroSAT's, in the zip the first run downloaded into `data`: {% $fig.tiles %} tiles from the Sentinel-2 satellite, each {% $fig.side %} by {% $fig.side %} pixels and {% $fig.metres %} across. Each tile is a JPEG in its kind's folder, such as `EuroSAT_RGB/Forest/Forest_1.jpg`, and there are {% $fig.kinds %} kinds. In `tiles.py`, write:

- `kinds(archive)`, the kinds of land use: the names of the folders that hold the zip's tiles, sorted. A kind's number is its place among them.
- `read(names, archive)`, the tiles at those names in the zip, decoded with Pillow, as a `uint8` tensor of shape `(N, 3, SIDE, SIDE)`, in red, green and blue. A tile in greys gives three equal channels, and a tile of another size is refused with a `ValueError`.
- `split(labelled, test, seed, archive)`, `labelled` tiles of each kind to learn from and `test` other tiles of each kind to test with, picked at random from `seed`. It gives each part as its tiles' names and their kinds' numbers, as an `int64` tensor. The same seed gives the same parts, whatever order the zip lists its tiles in, and a kind with fewer than `labelled + test` tiles is refused with a `ValueError`.

`archive` is `data/EuroSAT_RGB.zip` unless another is given.

```
kinds(archive) -> tuple of str
read(names, archive) -> uint8 tensor (N, 3, SIDE, SIDE)
split(labelled, test, seed, archive) -> (names, int64 tensor (N,)), (names, int64 tensor (N,))
```
