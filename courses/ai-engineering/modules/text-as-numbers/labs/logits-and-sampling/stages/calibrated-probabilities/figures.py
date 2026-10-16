import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit, log_expit

# The judge's probabilities the brief counts pairs above and below, and how far
# above the least log loss on the validation pairs a fit may come, as in the checks.
SURE, DOUBT, TOLERANCE = 0.99, 0.01, 0.001


def fit(margin, exact, shifted=True):
    """The slope and shift with the least log loss, or the slope alone with no shift."""

    def log_loss(parameters):
        slope, shift = parameters if shifted else (parameters[0], 0.0)
        scores = margin * slope + shift
        return -np.mean(np.where(exact, log_expit(scores), log_expit(-scores)))

    found = minimize(log_loss, x0=[1.0, 0.0] if shifted else [1.0]).x
    return (found[0], found[1]) if shifted else (found[0], 0.0)


def figures():
    pairs = pd.read_csv("data/logits.csv", keep_default_na=False)
    margin = (pairs["yes"] - pairs["no"]).to_numpy()
    exact = (pairs["label"] == "E").to_numpy()
    validation = (pairs["set"] == "validation").to_numpy()
    test = ~validation
    judge = expit(margin)
    slope, shift = fit(margin[validation], exact[validation])
    alone, _ = fit(margin[validation], exact[validation], shifted=False)
    share = exact[validation].mean()
    rows = {
        "raw": judge,
        "cal": expit(margin * slope + shift),
        "t": expit(margin * alone),
        "share": np.full(len(pairs), share),
    }
    sure = validation & (judge >= SURE)
    doubt = validation & (judge <= DOUBT)
    values = {
        "validation": str(validation.sum()),
        "test": str(test.sum()),
        "sure_cut": str(SURE),
        "val_sure": str(sure.sum()),
        "val_sure_exact": str(exact[sure].sum()),
        "doubt_cut": str(DOUBT),
        "val_doubt": str(doubt.sum()),
        "val_doubt_exact": str(exact[doubt].sum()),
        "tolerance": str(TOLERANCE),
        "temperature": f"{1 / slope:.2f}",
        "shift": f"{shift:.2f}".replace("-", "−"),
        "test_exact": str(exact[test].sum()),
        "lowest": f"{rows['cal'][test].min():.2f}",
        "highest": f"{rows['cal'][test].max():.2f}",
    }
    for name, probabilities in rows.items():
        brier = np.mean((probabilities[test] - exact[test]) ** 2)
        values[f"{name}_brier"] = f"{brier:.3f}"
        values[f"{name}_sum"] = f"{probabilities[test].sum():.1f}"
    return values
