`groupby` sets missing values aside by default. Grouped by `medical_specialty`, it would count only {% $fig.counted %} of the {% $fig.patients %} patients, because {% $fig.missing %} have no specialty recorded. `dropna=False` keeps them as a group of their own, and the counts add up to every patient.

```python
soon = table["readmitted"] == "<30"
rates = soon.groupby(table[by], dropna=False).agg(encounters="size", readmitted="sum")
rates["share"] = rates["readmitted"] / rates["encounters"]
```

`size` counts each group's rows and `sum` its `True` values, so the share is one over the other. A small group's share moves a long way with each patient: {% $fig.hmo_readmitted %} of the {% $fig.hmo %} patients referred by an HMO were readmitted, {% $fig.hmo_share %}, and one more or one fewer would move it by {% $fig.hmo_step %} points. A report leaves out the values with too few encounters to say much, as the chart's slider shows for the age groups.
