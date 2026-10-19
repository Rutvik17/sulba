`zipfile.ZipFile(archive).namelist()` gives every name in the zip, its folders' too: a folder's name ends in `/`. `PurePosixPath(name).parent.name` gives the folder a tile is in.

---

`Image.open(io.BytesIO(data))` opens a JPEG from its bytes, `.convert("RGB")` gives it three channels, and `np.asarray` gives its pixels in the shape `(rows, columns, channels)`. `.permute(0, 3, 1, 2)` puts a batch's channels first.

---

`random.Random(seed).sample(names, k)` picks `k` of the names at random. Sort the names first, so the tiles it picks depend only on the names and the seed.
