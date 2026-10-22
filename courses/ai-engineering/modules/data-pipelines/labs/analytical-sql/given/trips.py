"""Loads the city's taxi zones and days of August 2025's yellow cab trips into Postgres."""

import csv
import io
from datetime import datetime, time, timedelta

import psycopg
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv as pa_csv
import pyarrow.parquet as pq

TRIPS = "data/yellow_tripdata_2025-08.parquet"
ZONES = "data/taxi_zone_lookup.csv"

# Each column of the table trips: its name, the file's column it comes from, and its type.
COLUMNS = [
    ("vendor", "VendorID", "integer"),
    ("pickup_at", "tpep_pickup_datetime", "timestamp"),
    ("dropoff_at", "tpep_dropoff_datetime", "timestamp"),
    ("passengers", "passenger_count", "integer"),
    ("distance", "trip_distance", "numeric(10, 2)"),
    ("rate_code", "RatecodeID", "integer"),
    ("stored", "store_and_fwd_flag", "text"),
    ("pickup_zone", "PULocationID", "integer"),
    ("dropoff_zone", "DOLocationID", "integer"),
    ("payment", "payment_type", "integer"),
    ("fare", "fare_amount", "numeric(10, 2)"),
    ("extra", "extra", "numeric(10, 2)"),
    ("mta_tax", "mta_tax", "numeric(10, 2)"),
    ("tip", "tip_amount", "numeric(10, 2)"),
    ("tolls", "tolls_amount", "numeric(10, 2)"),
    ("improvement_surcharge", "improvement_surcharge", "numeric(10, 2)"),
    ("total", "total_amount", "numeric(10, 2)"),
    ("congestion_surcharge", "congestion_surcharge", "numeric(10, 2)"),
    ("airport_fee", "Airport_fee", "numeric(10, 2)"),
    ("cbd_congestion_fee", "cbd_congestion_fee", "numeric(10, 2)"),
]

# The ways a rider can pay, by their code in the trip records' data dictionary.
PAYMENTS = [
    (0, "Flex Fare trip"),
    (1, "Credit card"),
    (2, "Cash"),
    (3, "No charge"),
    (4, "Dispute"),
    (5, "Unknown"),
    (6, "Voided trip"),
]

# What the zone lookup writes where it has no borough, zone or service zone.
MISSING = {"N/A", "Unknown"}


def connect(url):
    """A connection to the database at url, in autocommit mode."""
    return psycopg.connect(url, autocommit=True)


def load(conn, days):
    """Creates the tables zones, payments and trips, and loads the trips picked up on each
    of days, each a datetime.date."""
    conn.execute(
        "CREATE TABLE zones (zone integer PRIMARY KEY, borough text, name text, "
        "service text)"
    )
    conn.execute(
        "CREATE TABLE payments (payment integer PRIMARY KEY, name text NOT NULL)"
    )
    columns = ", ".join(f"{name} {kind}" for name, _, kind in COLUMNS)
    conn.execute(f"CREATE TABLE trips ({columns})")
    with open(ZONES, encoding="utf-8", newline="") as file:
        zones = [
            [int(row["LocationID"])]
            + [
                None if row[key] in MISSING else row[key]
                for key in ("Borough", "Zone", "service_zone")
            ]
            for row in csv.DictReader(file)
        ]
    with conn.cursor().copy("COPY zones FROM STDIN") as copy:
        for row in zones:
            copy.write_row(row)
    with conn.cursor().copy("COPY payments FROM STDIN") as copy:
        for row in PAYMENTS:
            copy.write_row(row)
    table = picked_up(pq.read_table(TRIPS, columns=[c for _, c, _ in COLUMNS]), days)
    # Counts the file keeps as floats become whole numbers, as their columns are.
    for name in ("passenger_count", "RatecodeID"):
        index = table.schema.get_field_index(name)
        table = table.set_column(index, name, table[name].cast(pa.int64()))
    text = io.BytesIO()
    pa_csv.write_csv(table, text, pa_csv.WriteOptions(include_header=False))
    names = ", ".join(name for name, _, _ in COLUMNS)
    with conn.cursor().copy(f"COPY trips ({names}) FROM STDIN (FORMAT csv)") as copy:
        copy.write(text.getvalue())
    conn.execute("ANALYZE")


def picked_up(table, days):
    """The trips in table picked up on any of days."""
    pickup = table["tpep_pickup_datetime"]
    keep = pa.array([False] * len(table))
    for day in days:
        start = datetime.combine(day, time())
        on_day = pc.and_(
            pc.greater_equal(pickup, start),
            pc.less(pickup, start + timedelta(days=1)),
        )
        keep = pc.or_(keep, on_day)
    return table.filter(keep)
