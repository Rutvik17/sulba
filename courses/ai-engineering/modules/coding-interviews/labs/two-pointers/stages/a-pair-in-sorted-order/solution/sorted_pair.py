def sorted_pair(numbers, target):
    """The positions (i, j), i < j, of two numbers that add up to target, or None."""
    left, right = 0, len(numbers) - 1
    while left < right:
        total = numbers[left] + numbers[right]
        if total == target:
            return (left, right)
        if total < target:
            left += 1
        else:
            right -= 1
    return None
