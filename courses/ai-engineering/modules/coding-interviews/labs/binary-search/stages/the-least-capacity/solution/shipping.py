def least_capacity(weights, days):
    """The smallest capacity that ships every package, in order, within days."""

    def days_needed(capacity):
        needed, load = 1, 0
        for weight in weights:
            if load + weight > capacity:
                needed, load = needed + 1, 0
            load += weight
        return needed

    low, high = max(weights), sum(weights)
    while low < high:
        middle = (low + high) // 2
        if days_needed(middle) <= days:
            high = middle
        else:
            low = middle + 1
    return low
