import gzip


def read(name):
    with gzip.open(f"data/{name}") as file:
        return file.read()


def figures():
    images = read("train-images-idx3-ubyte.gz")
    count, rows, columns = (
        int.from_bytes(images[i : i + 4], "big") for i in (4, 8, 12)
    )
    train = read("train-labels-idx1-ubyte.gz")[8:]
    test = read("t10k-labels-idx1-ubyte.gz")[8:]
    # The count's bytes read least significant first.
    little = int.from_bytes(images[4:8], "little")
    assert len(images) - 16 == count * rows * columns
    pixels = count * rows * columns
    # The prose says every kind has as many photos as the first.
    assert all(
        part.count(kind) == part.count(0)
        for part in (train, test)
        for kind in range(10)
    )
    return {
        "train": f"{count:,}",
        "test": f"{len(test):,}",
        "count_bytes": " ".join(f"{byte:02X}" for byte in images[4:8]),
        "little": f"{little:,}",
        "bytes_mb": f"{pixels / 1e6:.1f} MB",
        "float_mb": f"{4 * pixels / 1e6:.1f} MB",
        "per_train": f"{train.count(0):,}",
        "per_test": f"{test.count(0):,}",
        "chance": f"{test.count(0) / len(test):.0%}",
    }
