```python
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
```

Merge sort counts as it sorts. Each half comes back sorted with its own inversions counted, so only the pairs across the halves are left, and the merge finds them: when the right half's next number is smaller than the left half's, it's smaller than every number still waiting in the left half, `len(left) - i` of them, since those are in order. Taking the left half's number on a tie keeps equal numbers from counting. The work is merge sort's, in proportion to n log n.

Checking every pair is the slow way: {% $fig.pairs %} pairs for the longest test.
