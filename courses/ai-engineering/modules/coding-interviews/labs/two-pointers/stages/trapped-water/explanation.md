```python
def trapped_water(heights):
    water = 0
    left, right = 0, len(heights) - 1
    left_high = right_high = 0
    while left < right:
        if heights[left] < heights[right]:
            left_high = max(left_high, heights[left])
            water += left_high - heights[left]
            left += 1
        else:
            right_high = max(right_high, heights[right])
            water += right_high - heights[right]
            right -= 1
    return water
```

The water above a bar is set by the lower of the highest bars on its two sides. When the left bar is lower than the right one, the right side has a bar at least as high as anything on the left, so the water above the left bar is `left_high` minus its height, whatever lies between. The same holds for the right when it's the lower. Each step settles one bar, so the whole takes time in proportion to the row, with no extra space.

Two lists of the highest bar so far, one from each end, give the same answer with space in proportion to the row. Scanning both sides afresh for each bar reads the whole row for every bar: {% $fig.reads %} reads for the longest test's {% $fig.bars %} bars, far past the time limit.
