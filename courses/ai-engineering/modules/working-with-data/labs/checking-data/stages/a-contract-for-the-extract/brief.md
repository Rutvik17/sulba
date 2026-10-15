Each month the network sends a new extract, and a pipeline checks it before any report or model uses it. The first check holds the extract to a contract, written from the dataset's documentation, which the starter holds:

- `COLUMNS`, the extract's {% $fig.columns %} columns;
- `MAY_BE_MISSING`, the columns the documentation says may be missing a value: in any other, a missing value is a problem;
- `ALLOWED`, the values the documentation gives five columns, as the extract spells them;
- `RANGES`, the ranges the dataset's inclusion criteria set for the length of stay, the lab tests and the medications.

Write `contract_problems`, which gives each rule the table breaks as `(column, problem, rows)`: the column `absent`, values `missing` where none may be, values `not allowed`, or values `out of range`, with how many rows break it. Go column by column in the contract's order. A missing value counts only as missing, and a value that isn't a number counts as out of range.

```
contract_problems(table) -> a list of (column, problem, rows), empty when the table keeps the contract
```
