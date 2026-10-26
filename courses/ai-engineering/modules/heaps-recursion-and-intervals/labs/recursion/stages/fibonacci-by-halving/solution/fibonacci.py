def fibonacci(n, modulus):
    def pair(n):
        if n == 0:
            return 0, 1
        a, b = pair(n // 2)
        even = a * (2 * b - a) % modulus
        odd = (a * a + b * b) % modulus
        return (odd, (even + odd) % modulus) if n % 2 else (even, odd)

    return pair(n)[0]
