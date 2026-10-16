import numpy as np

from judge import load_pairs, warp

# The temperatures drawn, the pairs drawn from, and the model's own temperature and
# top-k.
TEMPERATURES = [round(0.1 * step, 1) for step in range(1, 21)]
PAIRS, MODEL_TEMPERATURE, TOP_K = 200, 0.7, 20


def unlikeliest(logits, top_p):
    """For each temperature, the percentage of draws that aren't the likeliest token."""
    shares = []
    for temperature in TEMPERATURES:
        drawn = [warp(values, temperature, TOP_K, top_p).max() for values in logits]
        shares.append(round(100 * (1 - np.mean(drawn)), 4))
    return shares


def chart(top_p=0.8):
    _, _, logits = load_pairs()
    logits = logits[:PAIRS]
    at = TEMPERATURES.index(MODEL_TEMPERATURE)
    # The top-p chosen, and top-p 1 to read it against unless it is the one chosen.
    settings = [top_p] if top_p == 1 else [top_p, 1]
    shares = {setting: unlikeliest(logits, setting) for setting in settings}
    lines = [
        {
            "style": "main" if setting == top_p else "faint",
            "label": f"Top-p {setting:g}",
            "x": TEMPERATURES,
            "y": shares[setting],
        }
        for setting in reversed(settings)
    ]
    ranges = [
        f"with top-p {setting:g} from {shares[setting][0]:.2f}% to "
        f"{shares[setting][-1]:.2f}%"
        for setting in settings
    ]
    return {
        "x": {"min": 0, "max": 2, "step": 0.5, "label": "temperature"},
        "y": {"min": 0, "max": 25, "step": 5, "label": "% of draws"},
        "lines": lines,
        "points": [{"x": MODEL_TEMPERATURE, "y": shares[top_p][at]}],
        "readouts": [
            {
                "label": f"Top-p {setting:g}, temperature {MODEL_TEMPERATURE}",
                "value": f"{shares[setting][at]:.2f}%",
            }
            for setting in settings
        ],
        "description": (
            f"The percentage of draws that aren't the likeliest token, over {PAIRS} "
            f"pairs, at temperatures from {TEMPERATURES[0]} to {TEMPERATURES[-1]} with "
            f"top-k {TOP_K}: {' and '.join(ranges)}."
        ),
    }
