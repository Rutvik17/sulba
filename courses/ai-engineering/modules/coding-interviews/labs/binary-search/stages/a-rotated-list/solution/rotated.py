def rotated_search(numbers, value):
    """The position of value in numbers, a sorted list that was rotated, or None."""
    low, high = 0, len(numbers) - 1
    while low <= high:
        middle = (low + high) // 2
        if numbers[middle] == value:
            return middle
        if numbers[low] <= numbers[middle]:
            if numbers[low] <= value < numbers[middle]:
                high = middle - 1
            else:
                low = middle + 1
        elif numbers[middle] < value <= numbers[high]:
            low = middle + 1
        else:
            high = middle - 1
    return None
