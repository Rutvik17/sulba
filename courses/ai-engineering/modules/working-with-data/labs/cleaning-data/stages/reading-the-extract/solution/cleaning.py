"""Cleaning the hospital network's extract of encounters."""

import pandas as pd


def read_encounters(path):
    """The extract at path, with each value it marks as missing read as missing, and no
    other value."""
    return pd.read_csv(path, na_values=["?"], keep_default_na=False)


def missing_shares(table):
    """The share of each column's values that are missing, for the columns with any, from the
    most missing to the least."""
    shares = table.isna().mean()
    return shares[shares > 0].sort_values(ascending=False)
