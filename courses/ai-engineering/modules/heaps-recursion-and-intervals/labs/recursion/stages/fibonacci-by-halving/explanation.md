```python
def fibonacci(n, modulus):
    def pair(n):
        if n == 0:
            return 0, 1
        a, b = pair(n // 2)
        even = a * (2 * b - a) % modulus
        odd = (a * a + b * b) % modulus
        return (odd, (even + odd) % modulus) if n % 2 else (even, odd)

    return pair(n)[0]
```

The pair $F(k), F(k + 1)$ gives the pair for $2k$, by $F(2k) = F(k)\,(2F(k + 1) - F(k))$ and $F(2k + 1) = F(k)^2 + F(k + 1)^2$, and the pair for $2k + 1$ is one step along: $F(2k + 1)$ and $F(2k) + F(2k + 1)$. So each call halves n, and the tests' largest n takes {% $fig.calls %} calls.

Sums and products mod a number come out the same whether each number is taken mod it first or not, so the numbers stay below `modulus`. `2 * b - a` can be negative once they are, and Python's `%` still gives a number from 0 to `modulus - 1`: its result has "the same sign as its second operand (or zero)", in the words of the language reference.

Adding the numbers up one at a time is the slow way: {% $fig.largest %} additions for the tests' largest n.
