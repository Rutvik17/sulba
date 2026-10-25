import pyarrow.parquet as pq

YELLOW = "data/yellow_tripdata_2025-08.parquet"
GREEN = "data/green_tripdata_2025-08.parquet"


def figures():
    yellow = pq.read_table(YELLOW)
    green = pq.read_table(GREEN)
    return {
        "yellow": f"{yellow.num_rows:,}",
        "green": f"{green.num_rows:,}",
        "yellow_columns": str(yellow.num_columns),
        "green_columns": str(green.num_columns),
        "yellow_unreported": f"{yellow['passenger_count'].null_count:,}",
        "green_unreported": f"{green['passenger_count'].null_count:,}",
    }
