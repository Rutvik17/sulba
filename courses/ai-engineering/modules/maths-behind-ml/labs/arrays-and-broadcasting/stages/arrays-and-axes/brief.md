Start `similar.py`. A clinic keeps the measurements of its past breast mass samples, each with the diagnosis it was given: these are its records. For each new sample, the pathologist wants the records most like it, and what they turned out to be. Over this lab you build that search in NumPy.

A sample's measurements come from a digitized image of cells drawn from the mass with a fine needle. Each of {% $fig.measures %} measures of the cell nuclei, such as their radius, comes three ways, and the columns are named for them: `mean_radius` over the nuclei in the image, its standard error `radius_error`, and `worst_radius`, the mean of the three largest.

The lab's data is one array with a row per sample. Column 0 is 1 for a new sample and 0 for a record, column 1 is 1 for a malignant mass and 0 for a benign one, and the {% $fig.measurements %} measurements follow.

Write `split`, which returns the records' measurements and diagnoses, then the new samples' measurements and diagnoses. A comparison such as `table[:, 0] == 1` gives one `True` or `False` per row, and indexing the rows with it keeps those where it is `True`.

Then write `column_stats`, which returns each column's mean and standard deviation over the rows of an array, as scikit-learn's `StandardScaler` computes them: the standard deviation divides by the number of rows.

```
split(table) -> (records, diagnoses, new, new_diagnoses)
column_stats(X) -> (mean, std)
```

The tests load the data with `np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)`: {% $fig.rows %} rows of {% $fig.columns %} numbers: {% $fig.records %} records, {% $fig.records_malignant %} of them malignant, and {% $fig.new %} new samples, {% $fig.new_malignant %} of them malignant.
