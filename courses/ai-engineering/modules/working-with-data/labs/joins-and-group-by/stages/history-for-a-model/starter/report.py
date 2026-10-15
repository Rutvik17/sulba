def history(table, mapping):
    """For each encounter of table, from the same patient's encounters before it: how many there
    were, how many of them were followed by a readmission within 30 days, and the description of
    the last one's discharge. A row for each encounter, on the table's index, in its order."""
    raise NotImplementedError
