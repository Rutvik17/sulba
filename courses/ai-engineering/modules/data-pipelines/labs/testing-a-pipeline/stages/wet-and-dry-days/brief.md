With a row for each borough and day, the dispatcher's question can be put to the data. In `rain.py`, write two functions, each taking the table `daily` gives.

`wet_and_dry(daily)` gives a row for each borough: `wet_days` and `dry_days`, how many days of each it has, as bigints, and `wet_trips` and `dry_trips`, its mean clean pickups on them, as doubles. A day without weather counts as neither.

Wet days don't fall evenly through the week: {% $fig.wet_wednesdays %} of August's {% $fig.wet_days %} were Wednesdays. So `against_dry_days(daily)` compares each wet day with the dry days of the same weekday, in a row for each borough's wet day:

| Column | Type | Value |
| --- | --- | --- |
| `borough` | string | the borough |
| `day` | date | the wet day |
| `weekday` | string | its weekday |
| `rain_mm` | double | its rain |
| `trips` | bigint | the borough's clean pickups that day |
| `dry_days` | bigint | the borough's dry days of that weekday |
| `dry_trips` | double | its mean clean pickups on them |
| `change` | double | `trips / dry_trips - 1`, missing where `dry_trips` is missing or 0 |

```
wet_and_dry(daily) -> DataFrame
against_dry_days(daily) -> DataFrame
```
