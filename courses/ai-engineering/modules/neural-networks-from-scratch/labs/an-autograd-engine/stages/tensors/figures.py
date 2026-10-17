import json

# The office's network: a first layer of this many units over this many pixels, trained on
# batches of this many digits.
HIDDEN, PIXELS, BATCH = 64, 64, 64


def figures():
    cases = json.loads(open("references/tensors.json").read())["cases"]
    return {
        "batch": str(BATCH),
        # A product and a sum for each weight of each unit of each digit.
        "values": f"{2 * BATCH * HIDDEN * PIXELS:,}",
        "cases": str(len(cases)),
    }
