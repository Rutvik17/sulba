```python
def most_water(heights):
    best = 0
    left, right = 0, len(heights) - 1
    while left < right:
        best = max(best, min(heights[left], heights[right]) * (right - left))
        if heights[left] < heights[right]:
            left += 1
        else:
            right -= 1
    return best
```

The water between two lines is capped by the shorter one. Paired with any line closer in, the shorter line holds at most its own height times a smaller gap, so none of those pairs can beat the pair just measured, and the shorter line can be dropped. Each step measures one pair and drops one line, so the positions meet after `n - 1` steps: time in proportion to the row, and no extra space.

Trying every pair instead means {% $fig.pairs %} pairs for the longest test's {% $fig.lines %} lines, far past the time limit.
