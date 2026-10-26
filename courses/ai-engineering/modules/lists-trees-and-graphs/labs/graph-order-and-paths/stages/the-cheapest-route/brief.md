An airline flies between `cities` numbered from 0, and `flights` lists its flights `(start, end, fare)`, each one way, with a fare of 0 or more. A route from `source` to `target` takes one flight after another, and every city it lands in on the way is a stop. Write `cheapest`:

```
cheapest(cities, flights, source, target, stops) -> the lowest total fare of a route from
    source to target with at most `stops` stops, or -1 if there's none
```

With the flights `[(0, 1, 100), (1, 2, 100), (2, 3, 100), (0, 2, 500), (1, 3, 600)]`, the cheapest route from 0 to 3 costs 300 with 2 stops, through 1 and 2. With at most 1 stop it's 600, through 2, and with none there's no route. The tests' largest airline has {% $fig.cities %} cities and {% $fig.flights %} flights, and allows {% $fig.stops %} stops.
