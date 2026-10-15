def rates(connection, column, smallest):
    """For each value of the column of encounters named column, NULL included, the encounters,
    those readmitted within 30 days and their share, for the values with at least smallest
    encounters, from the highest share to the lowest. A name that isn't one of the table's
    columns raises a ValueError."""
    raise NotImplementedError
