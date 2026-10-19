`gzip.open(path).read()` gives the file's bytes, uncompressed, and `int.from_bytes(data[i : i + 4], "big")` reads 4 of them as a number, the most significant first. The magic number's last byte says how many sizes follow it.

---

`torch.frombuffer(bytearray(data), dtype=torch.uint8, offset=start)` gives the bytes from `start` on as a tensor, and `.reshape` puts them in the header's shape. Give it a `bytearray`: `bytes` can't be written to, and PyTorch warns about a tensor whose memory can't be.

---

`images.unsqueeze(1)` gives a batch of shape `(N, 1, rows, columns)`, and `.to(torch.float32) / 255` scales it.
