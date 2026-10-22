"""The number of help pages, and of the desk's tasks."""

import csv
import json
from pathlib import Path


def figures() -> dict[str, str]:
    with open(Path("data/passages.csv"), encoding="utf-8", newline="") as file:
        pages = {row["page"] for row in csv.DictReader(file)}
    tasks = json.loads(Path("data/tasks.json").read_text(encoding="utf-8"))
    return {"pages": f"{len(pages)}", "tasks": f"{len(tasks)}"}
