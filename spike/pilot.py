"""Spike: records one sample of each release, with multidoc2dial_replies.py's every release
set to one sample.

    python spike/pilot.py <folder> <llama-server> <file to write> <shard>/<shards> <downloads>
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "datasets"))
import multidoc2dial_replies as tool  # noqa: E402

for release in tool.RELEASES.values():
    release["samples"] = 1
folder, server, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
tool.record(folder, server, out, sys.argv[4], Path(sys.argv[5]))
