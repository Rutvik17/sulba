import json
from pathlib import Path


def figures():
    text = Path("references/validation.json").read_text(encoding="utf-8")
    groups = json.loads(text)["cases"]
    return {"cases": str(sum(len(cases) for cases in groups.values()))}
