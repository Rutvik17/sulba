A patient can come back many times: the {% $fig.encounters %} encounters belong to {% $fig.patients %} patients. The network wants to know how many patients come back within {% $fig.days %} days of leaving hospital, and `readmitted` records it for each encounter: `<30` for a readmission within {% $fig.days %} days, `>30` for a later one, and `NO` for none.

Count each patient once, at their first encounter: the one with the lowest `encounter_id`, wherever it comes in the table. Then leave out the encounters that ended in death or in hospice care, as the study behind the extract did. In `discharge_disposition_id`, codes {% $fig.death_codes %} are deaths, and {% $fig.hospice_codes %} hospice care.

Write `first_encounters`, `drop_deaths_and_hospice` and `readmitted_within_30_days`.

```
first_encounters(table) -> a DataFrame, one row per patient
drop_deaths_and_hospice(table) -> a DataFrame without those encounters
readmitted_within_30_days(table) -> a Series of True and False, one per encounter
```

An encounter whose discharge is unknown stays, and none of the three changes the table it's given. The tests run on the extract as `mark_unknown` marks it.
