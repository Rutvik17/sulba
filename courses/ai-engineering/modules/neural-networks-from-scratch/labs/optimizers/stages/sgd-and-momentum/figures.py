import json

# The momentum the explanation takes as its example.
MU = 0.9


def figures():
    cases = json.loads(open("references/steps.json").read())["sgd"]
    return {
        "cases": str(len(cases)),
        "mu": f"{MU:g}",
        "limit": f"{1 / (1 - MU):.0f}",
    }
