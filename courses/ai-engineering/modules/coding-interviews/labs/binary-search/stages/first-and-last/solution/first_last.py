def first_and_last(numbers, value):
    """The first and last positions of value in the sorted numbers, or None."""

    def boundary(past):
        low, high = 0, len(numbers)
        while low < high:
            middle = (low + high) // 2
            if numbers[middle] < value or (past and numbers[middle] == value):
                low = middle + 1
            else:
                high = middle
        return low

    first = boundary(past=False)
    if first == len(numbers) or numbers[first] != value:
        return None
    return (first, boundary(past=True) - 1)
