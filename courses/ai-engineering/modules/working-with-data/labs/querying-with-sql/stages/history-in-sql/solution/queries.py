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

HISTORY = """
SELECT e.encounter_id,
    COUNT(*) OVER earlier AS earlier_encounters,
    COALESCE(SUM(e.readmitted = '<30') OVER earlier, 0) AS earlier_readmissions,
    LAG(d.description) OVER by_patient AS previous_discharge
FROM encounters AS e
LEFT JOIN codes AS d
    ON d.column_name = 'discharge_disposition_id' AND d.code = e.discharge_disposition_id
WINDOW by_patient AS (PARTITION BY e.patient_nbr ORDER BY e.encounter_id),
    earlier AS (by_patient ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING)
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


def rates(connection, column, smallest):
    """For each value of the column of encounters named column, NULL included, the encounters,
    those readmitted within 30 days and their share, for the values with at least smallest
    encounters, from the highest share to the lowest. A name that isn't one of the table's
    columns raises a ValueError."""
    names = [row[1] for row in connection.execute("PRAGMA table_info(encounters)")]
    if column not in names:
        raise ValueError(f"encounters has no column {column!r}")
    query = f"""
        SELECT "{column}" AS value, COUNT(*) AS encounters,
            SUM(readmitted = '<30') AS readmitted, AVG(readmitted = '<30') AS share
        FROM encounters
        GROUP BY "{column}"
        HAVING COUNT(*) >= ?
        ORDER BY share DESC
    """
    return pd.read_sql_query(query, connection, params=(smallest,))


def history(connection):
    """For each encounter, from the same patient's encounters before it: how many there were,
    how many of them were followed by a readmission within 30 days, and the description of the
    last one's discharge, in order of encounter_id."""
    return pd.read_sql_query(HISTORY, connection)
