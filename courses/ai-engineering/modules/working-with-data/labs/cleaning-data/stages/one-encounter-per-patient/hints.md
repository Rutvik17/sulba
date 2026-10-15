`sort_values("encounter_id")` puts the encounters in order, and `drop_duplicates("patient_nbr")` keeps the first row it meets of each patient.

---

`isin(codes)` on `discharge_disposition_id` is `True` for the encounters to leave out, `~` turns each `True` to `False` and back, and `table[condition]` keeps the rows where the condition is `True`.
