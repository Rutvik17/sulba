A company that dispatches New York's yellow cabs wants to know where and when riders take them, so it can send drivers there before they're asked for. It has handed you August 2025's trip records, which the city's Taxi and Limousine Commission publishes and the lab fetches into `data/`. `trips.py`, which the lab gives you, loads days of them into Postgres: `load(conn, days)` creates three tables and loads the trips picked up on each `datetime.date` in `days`.

- `zones`: each of the city's {% $fig.zones %} taxi zones, with its number in `zone`, its `borough`, its `name` and its `service` zone. Zones 264 and 265, which the city's lookup marks as unknown and outside the city, have no borough.
- `payments`: each `payment` code a trip can have, with its `name`.
- `trips`: a row for each trip, among its columns `pickup_at` and `dropoff_at`, on New York's clocks, `pickup_zone` and `dropoff_zone`, `passengers`, `payment`, `fare` and `total`.

On 5 August 2025, {% $fig.trips %} trips began, {% $fig.unknown %} of them in a zone with no borough. In `zones.py`, write `busiest(conn, day, n)`, each borough's busiest zones on `day`:

- Count the trips picked up in each zone on `day`, from its first moment to just before the next midnight, and leave out the zones with no borough.
- Rank each borough's zones by those trips, the most first. Zones with as many trips share a rank, and the next rank counts every zone before it: two zones first, the next third. Keep the zones ranked `n` or better, all of them when several share a rank.
- Give each zone kept its borough, its number, its name, its trips, its share of its borough's trips that day as a fraction, the median fare of its trips, and its rank, in order of borough, rank and zone number.

Send `day` and `n` to Postgres as the query's parameters.

```
busiest(conn, day, n=3) -> list of (borough, zone, name, trips, share, median_fare, rank)
```
