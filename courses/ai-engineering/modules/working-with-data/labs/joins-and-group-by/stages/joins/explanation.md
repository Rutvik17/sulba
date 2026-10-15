`merge(..., how="left")` keeps every row of the table, the left one, and puts a missing value where the mapping has no row for its code. An inner join, `merge`'s default, would drop those encounters without a word.

`validate="many_to_one"` checks that each code appears once in the mapping, and raises `MergeError` if one doesn't: a code listed twice would match each of its encounters twice. Joining the admission sources on all three tables stacked together, in which each admission type's code appears three times, turns the {% $fig.encounters %} encounters into {% $fig.stacked %} rows.

`indicator=True` adds a column `_merge` saying where each row came from: `"left_only"` for a code the mapping lacks. This extract has none, but next month's could, and `unmatched` finds them before a report counts them as unknown.
