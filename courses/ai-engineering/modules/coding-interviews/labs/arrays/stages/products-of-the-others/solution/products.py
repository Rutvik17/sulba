def products_of_others(numbers):
    """A list whose item i is the product of every number but numbers[i]."""
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
