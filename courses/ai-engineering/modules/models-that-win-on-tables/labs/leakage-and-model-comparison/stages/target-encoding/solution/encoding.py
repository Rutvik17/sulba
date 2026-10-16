"""Target encoding: each category as its share of yes, learnt without each call's own
answer."""

import numpy as np
import pandas as pd


def encode(fit_values, fit_yes, values, smooth):
    """Each of values encoded by its share of yes among the fit calls, pulled toward the share
    of all of them by smooth. A value the fit calls never had gets the share of all of them."""
    prior = np.mean(fit_yes)
    groups = pd.Series(fit_yes).groupby(fit_values.to_numpy())
    shares = (groups.sum() + smooth * prior) / (groups.count() + smooth)
    return values.map(shares).fillna(prior).to_numpy(dtype=float)


def cross_fit(values, said_yes, splits, smooth):
    """Each call's encoding, learnt from the fit calls of the split that holds it out."""
    encoded = np.empty(len(values))
    for fit, held in splits:
        encoded[held] = encode(
            values.iloc[fit], said_yes[fit], values.iloc[held], smooth
        )
    return encoded
