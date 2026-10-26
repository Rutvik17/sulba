# The tests' largest n, and the brief's example, as tests/test_fibonacci.py sets them.
LARGEST = 10**18
MODULUS = 1_000_000_007


def figures():
    numbers = [0, 1]
    while len(numbers) < 1_002:
        numbers.append(numbers[-1] + numbers[-2])
    # The halving identities, checked exactly on every k they reach here.
    for k in range(500):
        assert numbers[2 * k] == numbers[k] * (2 * numbers[k + 1] - numbers[k])
        assert numbers[2 * k + 1] == numbers[k] ** 2 + numbers[k + 1] ** 2
    calls, n = 1, LARGEST
    while n:
        n //= 2
        calls += 1
    return {
        "hundred": f"{numbers[100] % MODULUS}",
        "largest": f"{LARGEST:,}",
        "calls": f"{calls}",
    }
