Joining two ropes into one costs the sum of their lengths, and the joined rope can be joined again. Write `join_cost`:

```
join_cost(lengths) -> the least cost of joining all the ropes into one
```

`join_cost([4, 3, 2, 6])` returns 29: join 2 and 3 for 5, then 4 and 5 for 9, then 6 and 9 for 15. No ropes, or one, cost nothing to join. The tests' longest list has {% $fig.ropes %} ropes.
