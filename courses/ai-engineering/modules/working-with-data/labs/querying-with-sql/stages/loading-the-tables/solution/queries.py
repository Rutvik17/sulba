"""The network's questions, asked in SQL."""


def load(connection, table, mapping):
    """Puts the encounters in a table encounters, a missing value as NULL, and the mapping in a
    table codes of column_name, code and description, keyed by column_name and code. Kept once
    the connection closes."""
    table.to_sql("encounters", connection, index=False)
    connection.execute(
        "CREATE TABLE codes (column_name TEXT, code INTEGER, description TEXT, "
        "PRIMARY KEY (column_name, code))"
    )
    rows = [
        (column, code, description)
        for column, codes in mapping.items()
        for code, description in zip(codes["code"], codes["description"], strict=True)
    ]
    connection.executemany("INSERT INTO codes VALUES (?, ?, ?)", rows)
    connection.commit()
