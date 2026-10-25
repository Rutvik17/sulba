Riders don't take cabs evenly through the month. The dispatcher wants each zone's pickups day by day, smoothed over a week, and each borough's busiest zones each day. Of the city's {% $fig.zones %} taxi zones, {% $fig.with_trips %} have clean pickups in August, and {% $fig.gaps %} of those have days with none. In `days.py`, write three functions.

`zones(spark)` reads the city's zone lookup, `data/taxi_zone_lookup.csv`: each zone's number as `zone`, an int, then its `borough` and its `name`, each missing where the lookup writes `N/A` or `Unknown`, as it does for zones 264 and 265.

`zone_days(flagged, zones)` takes your flagged trips and the zones, and gives a row for each zone and day with clean pickups:

| Column | Type | Value |
| --- | --- | --- |
| `zone` | int | the pickup zone |
| `borough` | string | its borough |
| `name` | string | its name |
| `day` | date | the day the trips were picked up |
| `trips` | bigint | the zone's clean pickups that day |
| `week` | double | the zone's mean trips a day over the seven days ending that day |

A day with no trips counts as 0 in the mean. A day before 7 August, whose seven days reach into July, has no `week`.

`busiest(zone_days, n)` gives each borough's `n` busiest zones each day by trips, with columns `borough`, `day`, `place`, `zone`, `name` and `trips`. Zones with as many trips share a place, and the next place counts every zone before it: two zones first, the next third. Keep every zone placed `n` or better.

```
zones(spark) -> DataFrame
zone_days(flagged, zones) -> DataFrame
busiest(zone_days, n=3) -> DataFrame
```
