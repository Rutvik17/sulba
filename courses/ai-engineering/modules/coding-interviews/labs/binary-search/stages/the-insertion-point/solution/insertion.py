def insertion_point(numbers, value):
    """The first position where value could go in the sorted numbers and keep them sorted."""
    low, high = 0, len(numbers)
    while low < high:
        middle = (low + high) // 2
        if numbers[middle] < value:
            low = middle + 1
        else:
            high = middle
    return low
