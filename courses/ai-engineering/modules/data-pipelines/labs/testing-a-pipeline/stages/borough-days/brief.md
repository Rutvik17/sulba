The dispatcher's question is about days: on a wet day, do more riders take cabs, and where? The rest of the lab works from one table, each borough's clean pickups on each day beside the day's weather.

The city's zone lookup, `data/taxi_zone_lookup.csv`, gives each pickup zone's borough: {% $fig.boroughs %} of them, counting EWR for Newark Airport, with `N/A` and `Unknown` for the two zones outside them. In `daily.py`, write three functions.

`august(spark)` gives every day of August 2025, one row each, as a date in `day`. `boroughs(spark)` gives each zone's number as `zone`, an int, and its `borough`, missing where the lookup writes `N/A` or `Unknown`.

`daily(spark, flagged, weather)` takes your flagged trips and the weather from `weather.py`, and gives a row for each day of August and each borough the lookup names:

| Column | Type | Value |
| --- | --- | --- |
| `day` | date | the day |
| `weekday` | string | its weekday, as in `Friday` |
| `borough` | string | the borough |
| `trips` | bigint | the borough's clean pickups that day |
| `rain_mm` to `haze` | | the day's weather, as `weather.py` gives it |
| `wet` | boolean | whether at least 1 mm of rain fell |

Every borough has a row on every day. A borough with no clean pickups on a day has 0 trips: Staten Island had none on {% $fig.empty_day %}. A day the weather lacks keeps its rows, with no weather, and is neither wet nor dry.

```
august(spark) -> DataFrame
boroughs(spark) -> DataFrame
daily(spark, flagged, weather) -> DataFrame
```
