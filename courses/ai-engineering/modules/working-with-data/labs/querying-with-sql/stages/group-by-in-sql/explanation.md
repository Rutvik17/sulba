```python
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
```

`GROUP BY` keeps `NULL` as a group of its own: in grouping, SQL treats every `NULL` as the same value, where pandas' `groupby` leaves missing values out unless told otherwise. `COUNT(*)` counts a group's rows, and `COUNT(medical_specialty)` only those that aren't `NULL`: it would count {% $fig.counted %} of the {% $fig.encounters %} encounters.

`SUM(readmitted = '<30') / COUNT(*)` would divide one whole number by another, which SQLite does in whole numbers: the share of all encounters would come out as {% $fig.whole %}. `AVG` gives the share as a fraction. `HAVING` filters groups after they're counted, as `WHERE` filters rows before.

The name goes into the SQL text, quoted as a name, only once it's one of the table's own columns, so text such as `age; DROP TABLE encounters` never reaches the database.
