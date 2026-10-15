import pandas as pd

# The documentation's spellings of three columns' values, as its variables table writes them.
DOCUMENTED = {
    "gender": ["male", "female", "unknown/invalid"],
    "age": [f"[{a}, {a + 10})" for a in range(0, 100, 10)],
    "readmitted": ["<30", ">30", "No"],
}


def figures():
    table = pd.read_csv("data/encounters.csv", na_values=["?"], keep_default_na=False)
    failing = {
        column: int((~table[column].isin(values)).sum())
        for column, values in DOCUMENTED.items()
    }

    def share(rows):
        """How many rows fail, as all of them when every row does."""
        return f"all {rows:,}" if rows == len(table) else f"{rows:,}"

    return {
        "columns": str(len(table.columns)),
        "gender_failing": share(failing["gender"]),
        "age_failing": share(failing["age"]),
        "no_failing": f"{failing['readmitted']:,}",
    }
