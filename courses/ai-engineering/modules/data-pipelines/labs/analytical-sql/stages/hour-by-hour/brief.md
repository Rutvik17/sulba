The dispatchers plan drivers' shifts by the hour. On 5 August, Midtown Center, zone 161, had {% $fig.busy_trips %} pickups, the most in one hour {% $fig.busy_peak %}, in the hour from {% $fig.busy_peak_hour %}. Williamsburg (North Side), zone 255, had {% $fig.quiet_trips %}, and none at all in {% $fig.empty %} of the day's hours.

In `hours.py`, write `hourly(conn, zone, day)`: a row for each of the 24 hours of `day`, from midnight, with

- `hour`: the hour's start, a `datetime`;
- `trips`: the trips picked up in `zone` in that hour, 0 in an hour with none;
- `running`: the zone's trips that day up to the end of the hour;
- `rolling`: the mean of `trips` over the hour and the two before it, or over as many as there are at the start of the day;
- `change`: `trips` less the hour before's, `None` for the first hour.

An hour without a trip has its row, and counts in the means and the changes as any other. Counts and changes come back as `int`s, and means as `float`s.

```
hourly(conn, zone, day) -> 24 rows of (hour, trips, running, rolling, change)
```
