Sort by `encounter_id` and group by `patient_nbr`. `died.groupby(patient).cumsum()` counts each patient's deaths up to each encounter, its own included, and `shift` gives each encounter the value of the one before.

---

The age groups in `ALLOWED["age"]` are in order, so `{age: rank for rank, age in enumerate(ALLOWED["age"])}` gives each its place to compare.
