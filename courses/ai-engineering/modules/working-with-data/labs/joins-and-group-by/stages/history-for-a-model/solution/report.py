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


def describe(table, mapping):
    """A copy of table with each code column's descriptions beside it, every encounter kept
    once, in its order."""
    described = table.copy()
    for column, codes in mapping.items():
        names = codes.rename(
            columns={"code": column, "description": column.removesuffix("_id")}
        )
        described = described.merge(
            names, on=column, how="left", validate="many_to_one"
        )
    return described


def unmatched(table, mapping):
    """For each code column, the codes in table that the mapping lacks, smallest first."""
    found = {}
    for column, codes in mapping.items():
        joined = table[[column]].merge(
            codes, left_on=column, right_on="code", how="left", indicator=True
        )
        lacking = joined.loc[joined["_merge"] == "left_only", column]
        found[column] = sorted(lacking.unique().tolist())
    return found


def readmission_rates(table, by, smallest):
    """For each value of the column by, a missing value included, the encounters, those
    readmitted within 30 days and their share, for the values with at least smallest
    encounters, from the highest share to the lowest."""
    soon = table["readmitted"] == "<30"
    rates = soon.groupby(table[by], dropna=False).agg(
        encounters="size", readmitted="sum"
    )
    rates["share"] = rates["readmitted"] / rates["encounters"]
    rates = rates[rates["encounters"] >= smallest]
    return rates.sort_values("share", ascending=False, kind="stable")


def history(table, mapping):
    """For each encounter of table, from the same patient's encounters before it: how many there
    were, how many of them were followed by a readmission within 30 days, and the description of
    the last one's discharge. A row for each encounter, on the table's index, in its order."""
    ordered = table.sort_values("encounter_id")
    patient = ordered["patient_nbr"]
    soon = ordered["readmitted"] == "<30"
    discharges = mapping["discharge_disposition_id"].set_index("code")["description"]
    discharge = ordered["discharge_disposition_id"].map(discharges)
    found = pd.DataFrame(
        {
            "earlier_encounters": soon.groupby(patient).cumcount(),
            "earlier_readmissions": soon.groupby(patient).cumsum() - soon,
            "previous_discharge": discharge.groupby(patient).shift(),
        }
    )
    return found.loc[table.index]
