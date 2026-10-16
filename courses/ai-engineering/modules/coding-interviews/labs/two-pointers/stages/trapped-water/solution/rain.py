def trapped_water(heights):
    """How much water the bars hold after rain."""
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
