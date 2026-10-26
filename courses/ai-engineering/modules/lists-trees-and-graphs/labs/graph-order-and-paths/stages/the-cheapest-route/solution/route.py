def cheapest(cities, flights, source, target, stops):
    """The lowest total price of a route from source to target with at most stops stops on
    the way, or -1 if there's no such route."""
    far = float("inf")
    price = [far] * cities
    price[source] = 0
    for _ in range(stops + 1):
        before = price[:]
        for start, end, fare in flights:
            if before[start] + fare < price[end]:
                price[end] = before[start] + fare
    return -1 if price[target] == far else price[target]
