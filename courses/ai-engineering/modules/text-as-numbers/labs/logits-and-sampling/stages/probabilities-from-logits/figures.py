import numpy as np
import pandas as pd

# The labels people gave the pairs, by the names the prose gives them.
LABELS = {
    "exact": "E",
    "substitutes": "S",
    "complements": "C",
    "irrelevant": "I",
}


def figures():
    pairs = pd.read_csv("data/logits.csv", keep_default_na=False)
    top = sum(column.startswith("logit_") for column in pairs.columns)
    tokens = pairs[[f"token_{i}" for i in range(1, top + 1)]].to_numpy()
    logits = pairs[[f"logit_{i}" for i in range(1, top + 1)]].to_numpy(dtype=float)
    lse = pairs["lse"].to_numpy()
    probabilities = np.exp(logits - lse[:, None])
    both = np.exp(pairs["yes"] - lse) + np.exp(pairs["no"] - lse)
    # The tokens other than Yes and No that take the most probability over all the
    # pairs.
    others = pd.Series(probabilities.ravel(), index=tokens.ravel())
    others = others.drop(["Yes", "No"]).groupby(level=0).sum().nlargest(2).index
    values = {
        "pairs": f"{len(pairs):,}",
        "top": str(top),
        "overflow": f"{np.log(np.finfo(float).max):.2f}",
        "first_yes": str((pairs["token_1"] == "Yes").sum()),
        "first_no": str((pairs["token_1"] == "No").sum()),
        "both_mean": f"{100 * both.mean():.2f}%",
        "both_min": f"{100 * both.min():.2f}%",
        "others": " and ".join(others),
        "kept_min": f"{100 * probabilities.sum(axis=1).min():.3f}%",
    }
    for name, label in LABELS.items():
        values[name] = str((pairs["label"] == label).sum())
    return values
