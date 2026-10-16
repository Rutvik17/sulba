def zero_triples(numbers):
    """Every different triple (a, b, c), a <= b <= c, that adds up to 0, in sorted order."""
    numbers = sorted(numbers)
    found = []
    for i, first in enumerate(numbers):
        if i > 0 and first == numbers[i - 1]:
            continue
        left, right = i + 1, len(numbers) - 1
        while left < right:
            total = first + numbers[left] + numbers[right]
            if total < 0:
                left += 1
            elif total > 0:
                right -= 1
            else:
                found.append((first, numbers[left], numbers[right]))
                left += 1
                while left < right and numbers[left] == numbers[left - 1]:
                    left += 1
                right -= 1
    return found
