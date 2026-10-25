from datetime import datetime

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

import report

# The columns each file keeps, in the order the publisher writes them.
ORDER = {
    "tpep": [
        "tpep_pickup_datetime",
        "payment_type",
        "fare_amount",
        "tip_amount",
        "total_amount",
        "congestion_surcharge",
        "cbd_congestion_fee",
    ],
    "lpep": [
        "lpep_pickup_datetime",
        "fare_amount",
        "tip_amount",
        "total_amount",
        "payment_type",
        "congestion_surcharge",
        "cbd_congestion_fee",
    ],
}
TYPES = {
    "payment_type": pa.int64(),
    "fare_amount": pa.float64(),
    "tip_amount": pa.float64(),
    "total_amount": pa.float64(),
    "congestion_surcharge": pa.float64(),
    "cbd_congestion_fee": pa.float64(),
}
# One plain green trip, on 5 August.
GREEN_TRIP = (datetime(2025, 8, 5, 14, 20), 1, 11.4, 2.0, 15.65, 0.0, 0.0)


def trip(at, payment=1, fare=12.1, tip=2.0, total=19.85, congestion=2.5, cbd=0.75):
    return (at, payment, fare, tip, total, congestion, cbd)


def write(tmp_path, monkeypatch, yellow, green=(GREEN_TRIP,)):
    """Points the report at files holding these trips, each a tuple in the order of trip()."""
    for name, prefix, trips in (("YELLOW", "tpep", yellow), ("GREEN", "lpep", green)):
        names = ["pickup", *TYPES]
        columns = dict(zip(names, zip(*trips, strict=True), strict=True))
        table = pa.table(
            {
                column: pa.array(
                    columns[
                        "pickup" if column.endswith("_pickup_datetime") else column
                    ],
                    pa.timestamp("us")
                    if column.endswith("_pickup_datetime")
                    else TYPES[column],
                )
                for column in ORDER[prefix]
            }
        )
        path = tmp_path / f"{prefix}.parquet"
        pq.write_table(table, path)
        monkeypatch.setattr(report, name, str(path))


def rows(spark):
    return {
        (row["service"], row["day"]): row.asDict()
        for row in report.daily_report(spark).collect()
    }


@pytest.mark.id("tst_qk49wg")
def test_green_columns(spark, tmp_path, monkeypatch):
    """Green's trips keep their own fares, tips and takings"""
    write(
        tmp_path,
        monkeypatch,
        [trip(datetime(2025, 8, 5, 9))],
        [
            (datetime(2025, 8, 5, 9), 2, 20.0, 0.0, 24.5, 0.0, 0.75),
            (datetime(2025, 8, 5, 11), 1, 8.6, 3.0, 13.6, 0.0, 0.0),
        ],
    )
    green = rows(spark)["green", 5]
    assert green["trips"] == 2
    assert green["fares"] == pytest.approx(28.6)
    assert green["tips"] == pytest.approx(3.0)
    assert green["takings"] == pytest.approx(38.1)


@pytest.mark.id("tst_z7125h")
def test_card_trips(spark, tmp_path, monkeypatch):
    """Only the trips paid by card count as card trips"""
    day = datetime(2025, 8, 5, 9)
    write(
        tmp_path,
        monkeypatch,
        [trip(day, payment=1), trip(day, payment=2), trip(day, payment=1)],
    )
    assert rows(spark)["yellow", 5]["card_trips"] == 2


@pytest.mark.id("tst_tjegce")
def test_missing_surcharge(spark, tmp_path, monkeypatch):
    """A trip with no congestion surcharge still has its CBD fee counted"""
    day = datetime(2025, 8, 5, 9)
    write(tmp_path, monkeypatch, [trip(day), trip(day, payment=0, congestion=None)])
    assert rows(spark)["yellow", 5]["charges"] == pytest.approx(4.0)


@pytest.mark.id("tst_s68e7k")
def test_august_only(spark, tmp_path, monkeypatch):
    """Trips picked up in July or September are no day of August's"""
    write(
        tmp_path,
        monkeypatch,
        [
            trip(datetime(2025, 7, 31, 23, 50)),
            trip(datetime(2025, 8, 1, 8)),
            trip(datetime(2025, 8, 31, 10)),
            trip(datetime(2025, 9, 1, 0, 10)),
        ],
    )
    result = rows(spark)
    assert result["yellow", 1]["trips"] == 1
    assert result["yellow", 31]["trips"] == 1
