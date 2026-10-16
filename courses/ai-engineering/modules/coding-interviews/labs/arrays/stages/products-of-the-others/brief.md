Write `products_of_others`:

```
products_of_others(numbers) -> a list whose item i is the product of every number but numbers[i]
```

`products_of_others([2, 3, 4, 5])` returns `[60, 40, 30, 24]`, and `products_of_others([2, 0, 4])` returns `[0, 8, 0]`. The product of no numbers is `1`, so a list of one number gives `[1]`.

Don't divide: dividing the product of all the numbers by each one fails on a zero. The tests' longest list has {% $fig.numbers %} numbers.
