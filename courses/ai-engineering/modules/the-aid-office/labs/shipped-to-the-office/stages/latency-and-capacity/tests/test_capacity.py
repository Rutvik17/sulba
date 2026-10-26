import pytest
from capacity import Timing, busy, per_hour, percentile, read

HEADER = "question,release,cache_n,prompt_n,prompt_ms,predicted_n,predicted_ms\n"


@pytest.mark.id("tst_xav8pn")
def test_read(tmp_path):
    """Times the first piece as the prompt and one token, and the whole reply"""
    path = tmp_path / "timings.csv"
    path.write_text(
        HEADER + "q1,five,80,1100,1500.0,100,8000.0\nq2,three,0,700,700.0,0,0.0\n"
    )
    assert read(path) == [
        Timing("q1", "five", pytest.approx(1.58), pytest.approx(9.5)),
        Timing("q2", "three", pytest.approx(0.7), pytest.approx(0.7)),
    ]


@pytest.mark.id("tst_rpqtwe")
def test_percentile():
    """Gives the smallest value that the share of the values are at or below"""
    values = [7, 1, 9, 3, 5, 2, 8, 4, 10, 6]
    assert percentile(values, 0.5) == 5
    assert percentile(values, 0.95) == 10
    assert percentile(values, 0.9) == 9
    assert percentile(values, 0.01) == 1
    assert percentile([4.5], 0.95) == 4.5


@pytest.mark.id("tst_79cxvk")
def test_per_hour():
    """Counts the replies an hour from the seconds each takes"""
    assert per_hour([2, 4]) == pytest.approx(1200)
    assert per_hour([3600]) == pytest.approx(1)


@pytest.mark.id("tst_vhn5i2")
def test_busy():
    """Gives the share of the peak hour spent replying"""
    assert busy(300, 600) == pytest.approx(0.5)
    assert busy(900, 600) == pytest.approx(1.5)


@pytest.mark.id("tst_qmdbd0")
def test_recorded():
    """Reads every recorded request, each release's questions in turn"""
    timings = read("data/timings.csv")
    assert [each.release for each in timings] == ["five"] * 224 + ["three"] * 224
    assert all(0 < each.first <= each.whole for each in timings)
