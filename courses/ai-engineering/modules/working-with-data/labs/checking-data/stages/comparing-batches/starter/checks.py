# The columns each month's extract is compared on with the month before's.
WATCHED = [
    "race",
    "gender",
    "age",
    "admission_type_id",
    "discharge_disposition_id",
    "admission_source_id",
    "readmitted",
]


def drift(previous, current, tolerance):
    """For each value of the watched columns, a missing value included, its share of the rows of
    previous and of current, and the change, for the values whose share changed by more than
    tolerance, the largest change first. A DataFrame of column, value, previous, current and
    change."""
    raise NotImplementedError
