"""Spike: joins CSV shards, in the order given, into one file with one header, and names any
shard that is missing.

    python spike/join.py <file to write> <shard>...
"""

import sys
from pathlib import Path

header = None
with open(sys.argv[1], "w", encoding="utf-8", newline="") as out:
    for path in map(Path, sys.argv[2:]):
        if not path.exists():
            print(f"missing: {path}")
            continue
        with open(path, encoding="utf-8", newline="") as file:
            first = file.readline()
            if header is None:
                header = first
                out.write(header)
            out.write(file.read())
