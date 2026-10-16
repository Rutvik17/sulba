Packages must ship in the order of a list of their weights, all whole numbers. Each day, a ship loads the next packages in order for as long as its load stays within its capacity, then sails. Write `least_capacity`:

```
least_capacity(weights, days) -> the smallest capacity that ships every package within days
```

`least_capacity([3, 2, 2, 4, 1, 4], 3)` returns `6`, which ships `[3, 2]`, `[2, 4]` and `[1, 4]`. There is at least one package and one day.

The tests' longest list has {% $fig.packages %} packages to ship in {% $fig.days %} days.
