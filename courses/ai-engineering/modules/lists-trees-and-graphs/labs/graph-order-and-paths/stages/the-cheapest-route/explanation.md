```python
def cheapest(cities, flights, source, target, stops):
    far = float("inf")
    price = [far] * cities
    price[source] = 0
    for _ in range(stops + 1):
        before = price[:]
        for start, end, fare in flights:
            if before[start] + fare < price[end]:
                price[end] = before[start] + fare
    return -1 if price[target] == far else price[target]
```

This is the Bellman-Ford algorithm, stopped after `stops + 1` rounds. After round `k`, each city's fare is the cheapest of the routes to it with at most `k` flights: every such route is its last flight after a route of at most `k - 1`, which the round before has priced. Reading the fares from `before`, the copy made at the start of the round, matters. A flight that read a fare lowered in the same round would chain two flights in one round, and the count of flights would no longer hold. With `f` flights it takes time in proportion to `(stops + 1) × f`.

Dijkstra's algorithm on the fares alone finds the cheapest route of any length, which may stop too often: on the brief's flights with 1 stop it would find 300, through two stops. Trying every route of at most `stops + 1` flights is the slow way: from a city with `d` flights out, the routes grow `d` times with each flight.
