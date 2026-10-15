"""The network's readmissions, by what each code means."""

import io

import pandas as pd


def read_mapping(path):
    """The ID mapping's tables, by the column each describes: each a DataFrame of code and
    description, the descriptions as written but for spaces around them."""
    with open(path) as file:
        sections = file.read().strip().split("\n,\n")
    tables = {}
    for section in sections:
        table = pd.read_csv(io.StringIO(section), keep_default_na=False)
        column = table.columns[0]
        tables[column] = pd.DataFrame(
            {"code": table[column], "description": table["description"].str.strip()}
        )
    return tables
