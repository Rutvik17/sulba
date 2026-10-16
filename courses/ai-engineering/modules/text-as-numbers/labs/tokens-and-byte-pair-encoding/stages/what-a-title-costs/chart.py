import pandas as pd

from bpe import costs, load_vocabulary

# The merges kept, from none to all of the shop's, and the test titles taken from each shop.
KEPT, PER_SHOP = range(0, 1001, 100), 100
NAMES = {"us": "US", "es": "Spain", "jp": "Japan"}
STYLES = {"us": "main", "es": "base", "jp": "faint"}


def chart():
    ranks = load_vocabulary()
    titles = pd.read_csv("data/titles.csv")
    test = titles[titles["set"] == "test"].groupby("shop").head(PER_SHOP)
    per_token = {shop: [] for shop in NAMES}
    for kept in KEPT:
        fewer = {token: rank for token, rank in ranks.items() if rank < 256 + kept}
        found = costs(test, fewer)
        for shop in NAMES:
            per_token[shop].append(round(float(found.loc[shop, "per_token"]), 6))
    kept = list(KEPT)
    return {
        "x": {"min": 0, "max": kept[-1], "step": 100, "label": "merges kept"},
        "y": {"min": 0, "max": 3, "step": 0.5, "label": "characters per token"},
        "lines": [
            {
                "style": STYLES[shop],
                "label": NAMES[shop],
                "x": kept,
                "y": per_token[shop],
            }
            for shop in ["jp", "es", "us"]
        ],
        "points": [{"x": kept[-1], "y": per_token[shop][-1]} for shop in NAMES],
        "readouts": [
            {
                "label": f"{NAMES[shop]}, characters per token, all merges",
                "value": f"{per_token[shop][-1]:.2f}",
            }
            for shop in NAMES
        ],
        "description": (
            f"Characters per token over {PER_SHOP} test titles from each shop, as the "
            f"tokenizer keeps from 0 to {kept[-1]:,} of its merges. US titles go from "
            f"{per_token['us'][0]:.2f} to {per_token['us'][-1]:.2f}, Spanish titles from "
            f"{per_token['es'][0]:.2f} to {per_token['es'][-1]:.2f}, and Japanese titles "
            f"from {per_token['jp'][0]:.2f} to {per_token['jp'][-1]:.2f}."
        ),
    }
