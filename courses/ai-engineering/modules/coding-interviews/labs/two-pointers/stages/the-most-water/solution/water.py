def most_water(heights):
    """The most water two of the lines can hold."""
    best = 0
    left, right = 0, len(heights) - 1
    while left < right:
        best = max(best, min(heights[left], heights[right]) * (right - left))
        if heights[left] < heights[right]:
            left += 1
        else:
            right -= 1
    return best
