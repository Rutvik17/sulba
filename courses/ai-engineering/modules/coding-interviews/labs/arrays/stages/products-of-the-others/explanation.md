```python
def products_of_others(numbers):
    products = [1] * len(numbers)
    before = 1
    for i, number in enumerate(numbers):
        products[i] = before
        before *= number
    after = 1
    for i in reversed(range(len(numbers))):
        products[i] *= after
        after *= numbers[i]
    return products
```

The first pass leaves the product of the numbers before each position in `products`, and the second multiplies in the product of the numbers after it, so each item ends up as the product of every number but its own. The two passes take time in proportion to the list, and the only space besides the answer is the two running products. A zero needs no special case: it makes every product it's part of `0`, and the product at its own position leaves it out.

Multiplying the other numbers afresh for each position instead takes {% $fig.multiplications %} multiplications for the longest test's {% $fig.numbers %} numbers, far past the time limit.
