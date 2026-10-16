A list holds a share's price at the close of each day, in order. Write `best_profit`, which finds the most one trade could have made:

```
best_profit(prices) -> the most made by buying on one day and selling on a later day, or 0
```

A trade buys one share and sells it on a later day. When no trade makes money, including when there are fewer than two days, the answer is `0`. `best_profit([9, 4, 6, 2, 8, 5])` returns `6`: buy at `2`, sell at `8`.

The tests' longest list has {% $fig.prices %} prices.
