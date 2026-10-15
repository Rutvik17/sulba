A window names each patient's rows, in order, and a frame picks the ones before the current row:

```sql
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
```

Without a frame, an ordered window runs from the patient's first row up to and including the current one, so `SUM` would count each encounter's own outcome: each of the {% $fig.soon %} encounters followed by a readmission would count its own. `ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING` stops at the row before. For a first encounter that frame holds no rows: `COUNT(*)` counts none, but `SUM` of no rows is `NULL`, which `COALESCE` replaces. `LAG` gives the value from the row before, `NULL` for a first encounter.

The window's `ORDER BY` decides the order, however the rows were stored. A subquery for each encounter, counting the patient's earlier encounters, would read the whole table again for every one of them; the window sorts the rows once.
