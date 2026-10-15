Each code column joins `codes` once, under a name of its own, and each join matches both halves of the key, the column's name and the code:

```sql
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
```

Without the column's name, an admission source's code would match the same code in each of the three code columns, and the {% $fig.encounters %} encounters would come back as {% $fig.unfiltered %} rows.

That condition belongs in `ON`. A `LEFT JOIN` keeps an encounter that matches no code, with `NULL` for the description. Put `s.column_name = 'admission_source_id'` in `WHERE` instead, and for that encounter it's `NULL` too, so `WHERE` drops the encounter: the left join acts as an inner one. `ON` decides which rows match; `WHERE` decides which rows stay.

Without `ORDER BY`, the order of the rows is undefined: SQLite promises none.
