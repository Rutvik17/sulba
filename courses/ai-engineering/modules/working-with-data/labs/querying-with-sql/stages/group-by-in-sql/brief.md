Now count in SQL. Write `rates`, which groups the encounters by the values of the column named `column` and gives each value's encounters, those readmitted within {% $fig.days %} days and their share, from the highest share to the lowest. A `NULL` is a group of its own, and values with fewer than `smallest` encounters are left out.

```
rates(connection, column, smallest) -> a DataFrame of value, encounters, readmitted and share
```

`smallest` goes to the database as a `?` parameter, but a column's name can't: a `?` stands only for a value. So check `column` against the names of the table's columns before it goes into the SQL, and refuse any other name with a `ValueError`.
