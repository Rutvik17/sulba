import json


def figures():
    cases = json.loads(open("references/scalars.json").read())["first_operations"]
    first = cases[0]["steps"]
    inputs = sum(step[0] == "input" for step in first)
    return {
        "cases": str(len(cases)),
        "inputs": str(inputs),
        "steps": str(len(first) - inputs),
    }
