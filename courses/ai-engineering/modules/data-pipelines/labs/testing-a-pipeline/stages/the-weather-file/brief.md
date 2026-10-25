The dispatcher from Spark DataFrames wants to know how the weather changes riding. This lab joins its trips, which `trips.py` and `flags.py` give you as that lab built them, to the taxi zones and to the weather at Central Park, and tests the pipeline that does it. Each test gets a Spark session, `spark`, which your functions take.

The weather comes from GHCN-Daily, NOAA's database of daily climate summaries from land stations across the globe. `data/central-park-2025-08.csv` is August 2025 at Central Park, station USW00094728, as NCEI's data service gives it: one row a day, {% $fig.days %} rows. Each value is a string padded with spaces, in tenths of its unit:

| Column | Value | Unit |
| --- | --- | --- |
| `PRCP` | the day's rain | tenths of a millimetre |
| `TMAX`, `TMIN` | its high and low | tenths of a degree Celsius |
| `AWND` | its mean wind speed | tenths of a metre a second |
| `WT01`, `WT03`, `WT08` | fog, thunder, haze | `1` on a day it was seen, empty on the others |

Beside each value, its `_ATTRIBUTES` column holds its flags and the time it was read, separated by commas: `MFLAG,QFLAG,SFLAG,TIME`. A measurement flag of `T` marks a trace, rain too little to measure, which the file gives as 0. The quality flag is blank for a value that passed every check, and a letter for one that failed, such as `O` for the climatological outlier check. No value in August's file failed one, and the code must still leave out a value that does.

In `weather.py`, write three functions. `attribute(column, position)` gives one of a value's attributes, an empty string where it has none. `measured(column)` gives a value in its units, a double, missing where its quality flag is set. `weather(spark)` reads the file into a row a day:

| Column | Type | Value |
| --- | --- | --- |
| `day` | date | the day |
| `rain_mm` | double | its rain in millimetres |
| `trace` | boolean | whether only a trace fell |
| `high_c` | double | its high in degrees Celsius |
| `low_c` | double | its low |
| `wind_ms` | double | its mean wind speed in metres a second |
| `fog`, `thunder`, `haze` | boolean | whether each was seen, false where the file leaves it empty |

Rain was measured on {% $fig.rain_days %} days of the month, and a trace fell on {% $fig.trace_days %} more.

```
attribute(column, position) -> Column
measured(column) -> Column
weather(spark) -> DataFrame
```
