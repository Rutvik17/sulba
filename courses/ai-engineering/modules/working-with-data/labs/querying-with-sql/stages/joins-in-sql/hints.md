Join `codes` once for each code column, under a name of its own, such as `codes AS s`, and match both the column's name and the code: `s.column_name = 'admission_source_id' AND s.code = e.admission_source_id`.

---

A `LEFT JOIN` keeps an encounter that matches no code. SQL gives rows in no set order unless the query ends with `ORDER BY`.
