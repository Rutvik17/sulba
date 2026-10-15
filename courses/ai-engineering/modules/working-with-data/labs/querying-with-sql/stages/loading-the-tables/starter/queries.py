"""The network's questions, asked in SQL."""


def load(connection, table, mapping):
    """Puts the encounters in a table encounters, a missing value as NULL, and the mapping in a
    table codes of column_name, code and description, keyed by column_name and code. Kept once
    the connection closes."""
    raise NotImplementedError
