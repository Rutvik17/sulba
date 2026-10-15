`cumcount` numbers each patient's rows in order, each by how many came before it. `cumsum` adds up their readmissions so far, and `shift` gives each row the value from the patient's row before it. All three work in the table's order, so sort by `encounter_id` first:

```python
def history(table, mapping):
    ordered = table.sort_values("encounter_id")
    patient = ordered["patient_nbr"]
    soon = ordered["readmitted"] == "<30"
    discharges = mapping["discharge_disposition_id"].set_index("code")["description"]
    discharge = ordered["discharge_disposition_id"].map(discharges)
    found = pd.DataFrame(
        {
            "earlier_encounters": soon.groupby(patient).cumcount(),
            "earlier_readmissions": soon.groupby(patient).cumsum() - soon,
            "previous_discharge": discharge.groupby(patient).shift(),
        }
    )
    return found.loc[table.index]
```

`cumsum` counts the encounter's own outcome too, and subtracting `soon` takes it off. `map` looks each code up in the descriptions and leaves a code they lack missing, as a left join would. Each column keeps the index of the rows it came from, and `.loc[table.index]` puts them back in the table's order. Joining columns on columns, `merge` ignores both tables' indexes and gives its result a new one, so a result built on it needs the table's index put back.

Of the {% $fig.encounters %} encounters, {% $fig.with_earlier %} have an earlier one in the extract, and the history matters: {% $fig.after_readmission %} of the encounters after an earlier readmission were followed by another within {% $fig.days %} days, against {% $fig.first_share %} of first encounters. Later encounters would say more, which is why the model mustn't see them: {% $fig.followed %} of the encounters followed by another of the same patient were readmitted within {% $fig.days %} days, against {% $fig.last %} of each patient's last. A readmission is itself a later encounter, so a count of all a patient's encounters would hand the model part of what it's meant to predict.
