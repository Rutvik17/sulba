from datetime import datetime, timedelta
from functools import cache

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
import pytest

from flags import FLAGS, flag_counts, flagged
from trips import trips

FILES = [
    ("data/yellow_tripdata_2025-08.parquet", "tpep"),
    ("data/green_tripdata_2025-08.parquet", "lpep"),
]
SCHEMA = (
    "service string, vendor int, pickup_at timestamp_ntz, dropoff_at timestamp_ntz, "
    "passengers int, distance double, pickup_zone int, dropoff_zone int, payment int, "
    "fare double, tip double, total double"
)
START = datetime(2025, 8, 1)
END = datetime(2025, 9, 1)


@cache
def expected():
    """Each flag's count over both files, worked out in pyarrow."""
    counts = dict.fromkeys([*FLAGS, "clean"], 0)
    for path, prefix in FILES:
        table = pq.read_table(path)
        pickup = table[f"{prefix}_pickup_datetime"]
        dropoff = table[f"{prefix}_dropoff_datetime"]
        unknown = pa.array([264, 265])
        flags = {
            "outside_month": pc.or_(
                pc.less(pickup, START), pc.greater_equal(pickup, END)
            ),
            "backwards": pc.less(dropoff, pickup),
            "too_long": pc.greater(
                dropoff, pc.add(pickup, pa.scalar(timedelta(hours=24)))
            ),
            "no_distance": pc.less_equal(table["trip_distance"], 0),
            "negative": pc.or_(
                pc.less(table["fare_amount"], 0), pc.less(table["total_amount"], 0)
            ),
            "unknown_zone": pc.or_(
                pc.is_in(table["PULocationID"], unknown),
                pc.is_in(table["DOLocationID"], unknown),
            ),
        }
        flags = {name: pc.fill_null(flag, False) for name, flag in flags.items()}
        for name, flag in flags.items():
            counts[name] += pc.sum(flag.cast(pa.int64())).as_py()
        any_flag = flags["outside_month"]
        for flag in list(flags.values())[1:]:
            any_flag = pc.or_(any_flag, flag)
        counts["clean"] += table.num_rows - pc.sum(any_flag.cast(pa.int64())).as_py()
    return counts


@pytest.mark.id("tst_wxbaas")
def test_counts(spark):
    """Each flag's count over the month's trips, and the clean ones"""
    assert flag_counts(flagged(trips(spark))) == expected()


@pytest.mark.id("tst_3tmzg7")
def test_columns(spark):
    """A boolean column for each flag, and clean, after the trip's own columns"""
    result = flagged(trips(spark))
    columns = trips(spark).columns
    assert result.columns == [*columns, *FLAGS, "clean"]
    assert {
        name: kind for name, kind in result.dtypes[len(columns) :]
    } == dict.fromkeys([*FLAGS, "clean"], "boolean")


@pytest.mark.id("tst_1ekaqo")
def test_missing_values(spark):
    """A missing value raises no flag, and every flag is true or false"""
    pickup = datetime(2025, 8, 5, 9, 30)
    rows = [
        ("yellow", 1, pickup, None, None, None, 161, 237, 1, None, None, None),
        (
            "green",
            2,
            pickup,
            pickup + timedelta(minutes=9),
            1,
            1.2,
            None,
            None,
            None,
            8.6,
            0.0,
            11.1,
        ),
    ]
    result = flagged(spark.createDataFrame(rows, SCHEMA)).collect()
    for row in result:
        assert [row[name] for name in FLAGS] == [False] * len(FLAGS)
        assert row["clean"] is True


@pytest.mark.id("tst_gdfwso")
def test_each_rule(spark):
    """Each rule on a trip made to break it, and a trip that breaks none"""
    pickup = datetime(2025, 8, 5, 9, 30)
    ok = (
        "yellow",
        1,
        pickup,
        pickup + timedelta(minutes=12),
        1,
        2.1,
        161,
        237,
        1,
        12.1,
        2.0,
        19.85,
    )
    broken = {
        "outside_month": {
            2: datetime(2025, 7, 31, 23, 59),
            3: datetime(2025, 8, 1, 0, 9),
        },
        "backwards": {3: pickup - timedelta(minutes=1)},
        "too_long": {3: pickup + timedelta(hours=24, seconds=1)},
        "no_distance": {5: 0.0},
        "negative": {11: -3.5},
        "unknown_zone": {7: 265},
    }
    rows = [ok]
    for changes in broken.values():
        row = list(ok)
        for index, value in changes.items():
            row[index] = value
        rows.append(tuple(row))
    result = (
        flagged(spark.createDataFrame(rows, SCHEMA))
        .orderBy("pickup_at", "dropoff_at")
        .collect()
    )
    marked = {tuple(name for name in FLAGS if row[name]) for row in result}
    assert marked == {(), *[(name,) for name in FLAGS]}
    assert [row["clean"] for row in result].count(True) == 1
