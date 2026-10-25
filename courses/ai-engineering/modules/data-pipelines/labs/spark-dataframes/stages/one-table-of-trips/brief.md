A company that dispatches New York's yellow and green cabs wants to know where and when riders take them. It has handed you August 2025's trip records, which the city's Taxi and Limousine Commission publishes and the lab fetches into `data/`: {% $fig.yellow %} yellow cab trips in `yellow_tripdata_2025-08.parquet` and {% $fig.green %} green cab trips in `green_tripdata_2025-08.parquet`. This lab works through them with Spark's DataFrame API. Each test gets a Spark session, `spark`, which your functions take.

The two files describe their trips in the same terms, but not in the same way. Yellow's pickup time is `tpep_pickup_datetime` and green's `lpep_pickup_datetime`, each file has columns the other lacks, and the columns they share come in a different order: yellow has {% $fig.yellow_columns %} columns and green {% $fig.green_columns %}. In `trips.py`, write `trips(spark)`: one DataFrame of every trip in both files, with these columns, in this order, of these types.

| Column | Type | From the file's |
| --- | --- | --- |
| `service` | string | `yellow` or `green`, by the file |
| `vendor` | int | `VendorID` |
| `pickup_at` | timestamp_ntz | `tpep_pickup_datetime` or `lpep_pickup_datetime` |
| `dropoff_at` | timestamp_ntz | `tpep_dropoff_datetime` or `lpep_dropoff_datetime` |
| `passengers` | int | `passenger_count` |
| `distance` | double | `trip_distance` |
| `pickup_zone` | int | `PULocationID` |
| `dropoff_zone` | int | `DOLocationID` |
| `payment` | int | `payment_type` |
| `fare` | double | `fare_amount` |
| `tip` | double | `tip_amount` |
| `total` | double | `total_amount` |

A value the file leaves out stays missing: {% $fig.yellow_unreported %} yellow trips and {% $fig.green_unreported %} green ones report no passengers.

```
trips(spark) -> DataFrame
```
