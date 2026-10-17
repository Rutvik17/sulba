import json


def figures():
    cases = json.loads(open("references/norms.json").read())["layer_norm"]
    return {"cases": str(len(cases))}
