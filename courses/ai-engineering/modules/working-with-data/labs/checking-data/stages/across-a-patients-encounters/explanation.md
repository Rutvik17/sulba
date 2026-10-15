Each problem compares an encounter with the patient's earlier ones: `cumsum` counts the deaths before it, once its own is taken off, and `shift` gives the age group and gender of the encounter before.

```python
ordered = table.sort_values("encounter_id")
patient = ordered["patient_nbr"]
died = ordered["discharge_disposition_id"].isin(DEATHS)
after_death = died.groupby(patient).cumsum() - died > 0
group = ordered["age"].map({age: rank for rank, age in enumerate(ALLOWED["age"])})
younger = group < group.groupby(patient).shift()
gender = ordered["gender"].groupby(patient).shift()
changed = gender.notna() & (ordered["gender"] != gender)
```

`gender.notna()` leaves out each patient's first encounter, which has no encounter before it to differ from. With the flags as columns beside each encounter, `melt` gives a row for each encounter and problem, and keeping the rows flagged leaves the problems.

Of the {% $fig.with_earlier %} encounters with an earlier one, {% $fig.after_death %} come after the patient's death, from {% $fig.after_death_patients %} patients, and {% $fig.younger %} are in a younger age group than the encounter before. Neither can be right as it stands: a death may be recorded on the wrong encounter, or the ids may not follow these patients' encounters in time, which taking the lowest `encounter_id` as the first encounter assumes. A check can find such rows but not say which value is wrong, so it holds them back and names them for someone who knows the records.
