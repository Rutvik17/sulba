def inversions(numbers):
    def count(items):
        if len(items) < 2:
            return items, 0
        middle = len(items) // 2
        left, left_count = count(items[:middle])
        right, right_count = count(items[middle:])
        merged, crossed = [], 0
        i = j = 0
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                merged.append(left[i])
                i += 1
            else:
                merged.append(right[j])
                crossed += len(left) - i
                j += 1
        merged += left[i:]
        merged += right[j:]
        return merged, left_count + right_count + crossed

    return count(list(numbers))[1]
