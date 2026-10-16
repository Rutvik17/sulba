"""Target encoding: each category as its share of yes, learnt without each call's own
answer."""

import numpy as np
import pandas as pd


def encode(fit_values, fit_yes, values, smooth):
    """Each of values encoded by its share of yes among the fit calls, pulled toward the share
    of all of them by smooth. A value the fit calls never had gets the share of all of them."""
    raise NotImplementedError


def cross_fit(values, said_yes, splits, smooth):
    """Each call's encoding, learnt from the fit calls of the split that holds it out."""
    raise NotImplementedError
