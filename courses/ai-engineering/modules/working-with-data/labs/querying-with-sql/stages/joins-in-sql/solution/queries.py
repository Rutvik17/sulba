"""The network's questions, asked in SQL."""

import pandas as pd

DESCRIBE = """
SELECT e.encounter_id,
    t.description AS admission_type,
    d.description AS discharge_disposition,
    s.description AS admission_source
FROM encounters AS e
LEFT JOIN codes AS t
    ON t.column_name = 'admission_type_id' AND t.code = e.admission_type_id
LEFT JOIN codes AS d
    ON d.column_name = 'discharge_disposition_id' AND d.code = e.discharge_disposition_id
LEFT JOIN codes AS s
    ON s.column_name = 'admission_source_id' AND s.code = e.admission_source_id
ORDER BY e.encounter_id
"""


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


def describe(connection):
    """Each encounter's id and the descriptions of its admission type, discharge and admission
    source, from the table codes, every encounter once, in order of encounter_id."""
    return pd.read_sql_query(DESCRIBE, connection)
