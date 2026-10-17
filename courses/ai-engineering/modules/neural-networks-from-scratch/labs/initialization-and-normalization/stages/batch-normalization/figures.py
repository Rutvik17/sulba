import json

# PyTorch's defaults for BatchNorm1d.
EPS, MOMENTUM = 1e-5, 0.1


def figures():
    cases = json.loads(open("references/norms.json").read())["batch_norm"]
    sizes = sorted(len(case["steps"][0]["X"]) for case in cases)
    return {
        "cases": str(len(cases)),
        "eps": f"{EPS:g}",
        "momentum": f"{MOMENTUM:g}",
        "kept": f"{1 - MOMENTUM:g}",
        "batches": " and ".join(str(len(case["steps"])) for case in cases),
        "small": str(sizes[0]),
        "large": str(sizes[-1]),
        "small_factor": f"{sizes[0] / (sizes[0] - 1):.2f}",
        "large_factor": f"{sizes[-1] / (sizes[-1] - 1):.2f}",
    }
