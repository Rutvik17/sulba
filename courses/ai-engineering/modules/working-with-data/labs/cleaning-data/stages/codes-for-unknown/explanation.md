The codes for unknown are the hospitals' way of recording no answer. Left as numbers, they'd count as types of admission and discharge of their own, and a count of missing values would never see them.

```python
marked[column] = marked[column].astype("Int64").mask(marked[column].isin(codes))
```

`isin` is `True` where a value is one of the codes, and `mask` puts a missing value there. A column of type `int64` can't hold a missing value: pandas would turn it into `float64`, and every code into a decimal. `Int64`, with a capital I, is pandas' integer type that can, and it shows a missing value as `<NA>`. Marked, {% $fig.admission_unknown %} of encounters have no admission type, {% $fig.discharge_unknown %} no discharge and {% $fig.source_unknown %} no admission source.

`dropna()` keeps only the rows with no missing value. On the marked extract it would keep {% $fig.complete %} of the encounters, because weight is missing from nearly all of them. Dropping a column that's mostly missing costs far less: without the columns missing in over {% $fig.high %} of encounters, {% $fig.complete_high %} of encounters are complete, and without those missing in over {% $fig.low %}, {% $fig.complete_low %}. How much of a column may be missing depends on what the table is for, so `drop_sparse` takes the limit as an argument.
