import pandas as pd

from sorter import MEASUREMENTS, choose_k

# The neighbours the chart compares, and the training beans it names, one in every few.
KS = [1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30, 40]
EVERY = 4


def chart(k):
    table = pd.read_csv("data/beans.csv")
    train, validation = table[table["set"] == 0], table[table["set"] == 1]
    a, varieties = train[MEASUREMENTS].to_numpy(), train["variety"].to_numpy()
    b, truth = validation[MEASUREMENTS].to_numpy(), validation["variety"].to_numpy()
    shares, best = choose_k(a, varieties, b, truth, KS)
    sample = slice(None, None, EVERY)
    themselves, _ = choose_k(a, varieties, a[sample], varieties[sample], KS)
    at = KS.index(k)
    return {
        "x": {"min": 0, "max": 40, "step": 5, "label": "k, the neighbours that vote"},
        "y": {"min": 0.85, "max": 1, "step": 0.05, "label": "share named right"},
        "lines": [
            {
                "style": "dashed",
                "label": "Training beans, each among its own neighbours",
                "x": KS,
                "y": [round(float(share), 6) for share in themselves],
            },
            {
                "style": "main",
                "label": "Validation beans",
                "x": KS,
                "y": [round(float(share), 6) for share in shares],
            },
        ],
        "points": [{"x": k, "y": round(float(shares[at]), 6)}],
        "readouts": [
            {
                "label": f"Validation beans named right with k = {k}",
                "value": f"{shares[at]:.1%}",
            },
            {
                "label": f"Training beans named right with k = {k}",
                "value": f"{themselves[at]:.1%}",
            },
            {"label": "Best k on the validation beans", "value": str(best)},
        ],
        "description": (
            f"The share of the {len(b)} validation beans your sorter names right for k from "
            f"{KS[0]} to {KS[-1]}, highest at k = {best}, beside the share of one in {EVERY} "
            f"training beans named right with each among its own neighbours, "
            f"{themselves[0]:.0%} at k = {KS[0]}. "
            f"With k = {k}, {shares[at]:.1%} of the validation beans are named right."
        ),
    }
