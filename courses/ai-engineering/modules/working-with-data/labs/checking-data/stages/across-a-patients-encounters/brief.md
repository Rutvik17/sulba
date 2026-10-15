Some of a patient's encounters can't all be right at once. Write `encounter_problems`, which compares each encounter with the patient's earlier ones, in order of `encounter_id`, and finds:

- `after a death`: an encounter after one of the patient's that ended in death, the discharge codes {% $fig.death_codes %}, which the starter holds as `DEATHS`;
- `younger`: an encounter in a younger age group than the patient's encounter before it;
- `gender changed`: an encounter whose gender differs from the patient's encounter before it.

```
encounter_problems(table) -> a DataFrame of encounter_id, patient_nbr and problem, in order of encounter_id
```

An encounter with more than one problem has a row for each, in the order above.
