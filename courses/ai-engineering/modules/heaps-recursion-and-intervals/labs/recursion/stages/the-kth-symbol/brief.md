Row 1 of a table is `0`. Each row after it is the row before with every `0` written as `01` and every `1` as `10`, so rows 2 to 4 are `01`, `0110` and `01101001`. Write `symbol`:

```
symbol(row, place) -> the symbol at that place in that row, 0 or 1, counting places from 1
```

`symbol(4, 5)` returns 1. The tests ask about rows up to row {% $fig.rows %}, which has {% $fig.length %} symbols.
