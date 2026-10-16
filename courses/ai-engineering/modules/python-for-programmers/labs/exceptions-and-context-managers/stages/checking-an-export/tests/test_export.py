import pytest

from errors import Number, Object, String, check_export

SAMPLE = Object({"id": String(), "radius": Number()})
DAY = [
    '{"id": "S1", "radius": 17.99}\n',
    '{"id": "S2", "radius": "x"}\n',
    '{"id": "S3", "radius": 13.54\n',
    '{"id": "S4", "radius": 11.42}\n',
    '{"id": "S5", "radius": 20.29, "note": "repeat"}\n',
    '{"id": "S6", "radius": 12.45}\n',
]


def export(folder, lines, name="2026-10-16.jsonl"):
    path = folder / name
    path.write_text("".join(lines), encoding="utf-8")
    return path


@pytest.mark.id("tst_tg849d")
def test_records(tmp_path):
    """Gives the records of an export that passes"""
    path = export(tmp_path, [DAY[0], DAY[3], DAY[5]])
    assert check_export(path, SAMPLE) == [
        {"id": "S1", "radius": 17.99},
        {"id": "S4", "radius": 11.42},
        {"id": "S6", "radius": 12.45},
    ]
    assert check_export(export(tmp_path, [], "2026-10-17.jsonl"), SAMPLE) == []


@pytest.mark.id("tst_zq457l")
def test_group(tmp_path):
    """Raises the failing lines together, noted with the export's name"""
    with pytest.raises(ExceptionGroup) as raised:
        check_export(export(tmp_path, DAY), SAMPLE)
    assert raised.value.message == "3 of 6 lines failed"
    assert raised.value.__notes__ == ["Export 2026-10-16.jsonl"]


@pytest.mark.id("tst_l6sk81")
def test_missing(tmp_path):
    """Lets a missing export's error go on"""
    with pytest.raises(FileNotFoundError):
        check_export(tmp_path / "2026-10-18.jsonl", SAMPLE)
