"""Cleaning the hospital network's extract of encounters."""

import pandas as pd


def read_encounters(path):
    """The extract at path, with each value it marks as missing read as missing, and no
    other value."""
    raise NotImplementedError


def missing_shares(table):
    """The share of each column's values that are missing, for the columns with any, from the
    most missing to the least."""
    raise NotImplementedError
