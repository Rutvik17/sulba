import zipfile
from collections import Counter
from pathlib import PurePosixPath

from PIL import Image

# A pixel of Sentinel-2's red, green and blue bands, which EuroSAT's tiles are made from, covers
# 10 m by 10 m (Helber et al., "EuroSAT", 2019, Table I).
METRES = 10


def figures():
    with zipfile.ZipFile("data/EuroSAT_RGB.zip") as zip_file:
        names = [name for name in zip_file.namelist() if name.endswith(".jpg")]
        with zip_file.open(names[0]) as file, Image.open(file) as image:
            width, height = image.size
    assert width == height
    folders = [PurePosixPath(name).parent.name for name in names]
    counts = Counter(folders)
    listed = list(dict.fromkeys(folders))
    every = sorted(counts)
    pixels = len(names) * 3 * width * height
    return {
        "tiles": f"{len(names):,}",
        "side": f"{width}",
        "metres": f"{width * METRES} m",
        "kinds": f"{len(every)}",
        "most": f"{max(counts.values()):,}",
        "fewest": f"{min(counts.values()):,}",
        "smallest": min(every, key=counts.get),
        "first_listed": listed[0],
        "first_sorted": every[0],
        "moved": f"{sum(a != b for a, b in zip(listed, every, strict=True))}",
        "bytes_mb": f"{pixels / 1e6:,.0f} MB",
        "float_gb": f"{4 * pixels / 1e9:.1f} GB",
        "chance": f"{1 / len(every):.0%}",
    }
