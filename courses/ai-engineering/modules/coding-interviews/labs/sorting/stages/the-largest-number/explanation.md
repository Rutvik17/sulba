```python
from functools import cmp_to_key


def largest_number(numbers):
    def order(a, b):
        if a + b > b + a:
            return -1
        return 1 if a + b < b + a else 0

    digits = sorted(map(str, numbers), key=cmp_to_key(order))
    return "".join(digits).lstrip("0") or "0"
```

Two numbers next to each other can always be swapped, so in the largest result each pair is in the order that writes the larger number: `a` before `b` when `a + b` is the larger string. This comparison orders all the numbers consistently, so sorting by it gives the largest result. The strings compare digit by digit, which matches comparing the numbers, since `a + b` and `b + a` have the same length. Sorting takes `$n \log n$` comparisons, each of two short strings.

Stripping leading zeros turns `"00"` into `"0"`. Converting with `int()` would do the same, but Python refuses to turn a string of more than 4,300 digits into a number, and the longest test's answer is longer. Trying every order instead means `$n!$` orders: far past the time limit for any list longer than a dozen numbers.
