Start `report.py`. The network wants its readmissions by what each code means: by admission type, discharge and admission source, in words. `data/ids-mapping.csv` holds the words as three tables in one file, one after another. Each starts with a header, the code column's name and `description`, and a line holding only a comma separates each from the next.

Write `read_mapping`, which reads the file into a table for each code column, of each code and its description.

```
read_mapping(path) -> a dict of DataFrames, by the column each describes
```

The codes are whole numbers, in the file's order. Keep each description as written, `NULL` included, but without the spaces around it: {% $fig.spaced %} of the {% $fig.sources %} admission sources start with one.
