The company's dashboards read each day's figures by zone from a table, and its scheduler will run your code each morning for the day before, or again for any day whose trips change. In `summary.py`, write `refresh(conn, day)`, which writes `day`'s rows into `daily_zones`, creating the table first if it isn't there:

| column | type | holds |
| --- | --- | --- |
| `day` | `date` | the day |
| `zone` | `integer` | the zone's number |
| `pickups` | `integer` | the trips picked up there that day |
| `dropoffs` | `integer` | of those trips, the ones that ended there |
| `revenue` | `numeric(12,2)` | the `total` of the trips picked up there |

No column can be null, and `(day, zone)` is the table's primary key. A zone has a row when one of the day's trips began or ended there, which on 5 August was {% $fig.zones %} zones, {% $fig.dropoffs_only %} of them with drop-offs alone. `refresh` returns how many zones it wrote.

The day's rows are written whole: a run again replaces them with the day as its trips are now, leaving no row of an earlier run; a run that fails partway leaves the rows as they were; and no run touches another day's rows.

```
refresh(conn, day) -> the number of zones written
```

Two tests run on every attempt. Then five checks run before the code ships.
