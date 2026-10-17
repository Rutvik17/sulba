The take-home's model learned from the extract's columns as they came, and its endpoint passed each request's fields straight to it. The service needs one place where both are made: the inputs the model learns from, and the inputs it's given for each stay a planner sends. Start `features.py`.

`stays` is the take-home's, as it was: the {% $fig.stays %} first stays, without deaths and hospice care. Write:

```
features(rows) -> a new DataFrame with the index of rows, holding the model's inputs for each
    row: stays from the extract, or the stays requests send
```

Its columns are `INPUTS`, in that order:

- the eight counts in `COUNTS`, as they are;
- `age`, the middle of the stay's age band: `75` for `[70-80)`;
- the eight columns in `CATEGORIES`, each value as text, so `admission_source_id` 7 becomes `"7"`.

A request brings a stay's fields as JSON, with the field names the extract uses: counts as numbers, categories as text, and codes such as `admission_source_id` as numbers, or as text when a client sends `"7"`. Whichever it is, `features` gives the stay the inputs its row in the extract gets. It leaves `rows` as they were.
