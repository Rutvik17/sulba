`struct.unpack("<Q", file.read(8))` gives the header's length: `<` for little-endian, `Q` for an unsigned 64-bit integer. Then `json.loads(file.read(length))` gives the header, and `pop("__metadata__", None)` takes the metadata out.

---

Read everything after the header into one `bytearray`. `torch.frombuffer(buffer, dtype=torch.float32, offset=begin, count=(end - begin) // 4)` makes a tensor of those numbers without copying them, and `.reshape(shape)` gives it its shape.

---

`header` needs only the start of the file: read the length and the header, and stop there.
